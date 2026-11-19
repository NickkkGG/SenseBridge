"""train.py - latih model bibir (LipNet di lipcore.py) dari klip hasil rekaman

Dipanggil tombol "Latih model":  train.train(lang, epochs=50, log=...)
  - membaca dataset/<lang>/<kata>/*.npy (24 frame 48x48 dari Rekam klip / record.py)
  - menyisihkan sebagian klip tiap kata untuk uji, lalu melatih LipNet dengan augmentasi
  - menyimpan model dengan akurasi uji terbaik ke models/lip_<lang>.pt

Dari terminal:  python train.py id 50
"""
import glob
import os
import sys

import numpy as np
import torch
import torch.nn as nn

import lipcore as lc

MIN_CLIPS = 5        # kata dengan klip lebih sedikit dari ini dilewati
VAL_SHARE = 0.2      # bagian klip tiap kata yang disisihkan untuk uji
BATCH = 16
LR = 1e-3


def _load(lang, log, tr):
    """{kata: [klip, ...]} untuk kata yang klipnya cukup, urut abjad."""
    root = os.path.join(lc.DATA_DIR, lang)
    data = {}
    for word in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        clips = []
        for path in sorted(glob.glob(os.path.join(root, word, "*.npy"))):
            try:
                clip = np.load(path)
            except (OSError, ValueError):
                continue
            if clip.ndim == 3 and clip.shape[1:] == (lc.IMG, lc.IMG) and len(clip) >= 2:
                clips.append(clip)
        if len(clips) >= MIN_CLIPS:
            data[word] = clips
        elif clips:
            log(tr(f"Lewati '{word}': baru {len(clips)} klip (minimal {MIN_CLIPS}).",
                   f"Skipping '{word}': only {len(clips)} clips (need {MIN_CLIPS})."))
    return data


def _augment(clip, rng):
    """Variasi acak supaya model tidak menghafal klip: tempo, posisi, cermin, terang."""
    n = int(rng.integers(int(len(clip) * 0.8), len(clip) + 1))   # prep() meregangkan lagi
    start = int(rng.integers(0, len(clip) - n + 1))
    clip = clip[start:start + n].astype(np.float32)
    dy, dx = rng.integers(-3, 4, size=2)
    clip = np.roll(clip, (int(dy), int(dx)), axis=(1, 2))
    if rng.random() < 0.5:
        clip = clip[:, :, ::-1]
    return clip * rng.uniform(0.8, 1.2) + rng.uniform(-20, 20)


def _batch(clips):
    return torch.stack([lc.prep(c) for c in clips])          # B,1,T,H,W


def train(lang, epochs=50, log=print):
    def tr(id_text, en_text):
        return id_text if lang == "id" else en_text

    data = _load(lang, log, tr)
    if len(data) < 2:
        have = ", ".join(f"{w} ({len(c)})" for w, c in data.items()) or "-"
        return tr(f"Error: butuh minimal 2 kata yang masing-masing punya {MIN_CLIPS}+ klip "
                  f"(termasuk {lc.SILENCE}). Yang ada: {have}.",
                  f"Error: need at least 2 words with {MIN_CLIPS}+ clips each "
                  f"(including {lc.SILENCE}). Found: {have}.")
    labels = list(data)
    if lc.SILENCE not in labels:
        log(tr(f"Catatan: belum ada kelas {lc.SILENCE}, jadi model akan selalu menebak suatu kata.",
               f"Note: no {lc.SILENCE} class yet, so the model will always guess some word."))

    rng = np.random.default_rng(0)
    train_set, val_set = [], []
    for i, word in enumerate(labels):
        clips = [data[word][j] for j in rng.permutation(len(data[word]))]
        n_val = max(1, round(len(clips) * VAL_SHARE))
        val_set += [(c, i) for c in clips[:n_val]]
        train_set += [(c, i) for c in clips[n_val:]]
    x_val = _batch([c for c, _ in val_set])
    y_val = torch.tensor([i for _, i in val_set])
    log(tr(f"Melatih {len(labels)} kata: {len(train_set)} klip latih, "
           f"{len(val_set)} klip uji, {epochs} epoch.",
           f"Training {len(labels)} words: {len(train_set)} training clips, "
           f"{len(val_set)} test clips, {epochs} epochs."))

    torch.manual_seed(0)
    model = lc.LipNet(len(labels))
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    best_acc, best_state = -1.0, None
    for epoch in range(1, epochs + 1):
        model.train()
        order = rng.permutation(len(train_set))
        loss_sum = 0.0
        for start in range(0, len(order), BATCH):
            items = [train_set[k] for k in order[start:start + BATCH]]
            x = _batch([_augment(c, rng) for c, _ in items])
            y = torch.tensor([i for _, i in items])
            opt.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            loss_sum += loss.item() * len(items)
        model.eval()
        with torch.no_grad():
            acc = float((model(x_val).argmax(1) == y_val).float().mean())
        if acc >= best_acc:                 # simpan yang terbaik (yang terbaru kalau seri)
            best_acc = acc
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        if epoch == 1 or epoch % 5 == 0 or epoch == epochs:
            log(f"Epoch {epoch}/{epochs}  loss {loss_sum / len(train_set):.3f}  "
                + tr(f"uji {acc:.0%}", f"test {acc:.0%}"))

    model.load_state_dict(best_state)
    model.eval()
    lc.save_model(lang, model, labels)
    return tr(f"Selesai: model {len(labels)} kata disimpan (akurasi uji terbaik {best_acc:.0%}).",
              f"Done: model for {len(labels)} words saved (best test accuracy {best_acc:.0%}).")


if __name__ == "__main__":
    print(train(sys.argv[1] if len(sys.argv) > 1 else "id",
                epochs=int(sys.argv[2]) if len(sys.argv) > 2 else 50))
