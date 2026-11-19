"""lipcore.py - deteksi mulut + model bibir (CNN 3D + GRU)"""
import os

import cv2
import mediapipe as mp
import numpy as np
import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "dataset")
MODEL_DIR = os.path.join(HERE, "models")
SEQ_LEN = 24          # jumlah frame per klip
IMG = 48              # ukuran crop mulut (piksel)
SILENCE = "_diam"     # kelas "tidak bicara"

mp_face = mp.solutions.face_mesh
LIPS = (61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269,
        267, 0, 37, 39, 40, 185)


def get_mouth_roi(frame, lm):
    """Return (roi grayscale IMGxIMG atau None, (x1, y1, x2, y2))."""
    H, W = frame.shape[:2]
    xs = [lm[i].x * W for i in LIPS]
    ys = [lm[i].y * H for i in LIPS]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    half = max(max(xs) - min(xs), max(ys) - min(ys)) * 0.75
    half = max(half, 16)
    x1, y1 = int(max(0, cx - half)), int(max(0, cy - half))
    x2, y2 = int(min(W, cx + half)), int(min(H, cy + half))
    crop = frame[y1:y2, x1:x2]
    if crop.shape[0] < 4 or crop.shape[1] < 4:
        return None, (x1, y1, x2, y2)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, (IMG, IMG)), (x1, y1, x2, y2)


class LipNet(nn.Module):
    def __init__(self, n_classes):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv3d(1, 16, (3, 5, 5), padding=(1, 2, 2)),
            nn.BatchNorm3d(16), nn.ReLU(), nn.MaxPool3d((1, 2, 2)),
            nn.Conv3d(16, 32, 3, padding=1),
            nn.BatchNorm3d(32), nn.ReLU(), nn.MaxPool3d((1, 2, 2)),
            nn.Conv3d(32, 64, 3, padding=1),
            nn.BatchNorm3d(64), nn.ReLU(), nn.MaxPool3d((1, 2, 2)),
        )
        self.gru = nn.GRU(64 * 6 * 6, 128, batch_first=True, bidirectional=True)
        self.drop = nn.Dropout(0.4)
        self.fc = nn.Linear(256, n_classes)

    def forward(self, x):                 # x: B,1,T,H,W
        x = self.conv(x)                  # B,64,T,6,6
        B, C, T, H, W = x.shape
        x = x.permute(0, 2, 1, 3, 4).reshape(B, T, C * H * W)
        x, _ = self.gru(x)
        return self.fc(self.drop(x.mean(1)))


def prep(clip):
    """clip: array (T,H,W) -> tensor (1,T,H,W), dinormalisasi."""
    clip = np.asarray(clip, dtype=np.float32)
    if len(clip) != SEQ_LEN:
        idx = np.linspace(0, len(clip) - 1, SEQ_LEN).round().astype(int)
        clip = clip[idx]
    clip = clip / 255.0
    clip = (clip - clip.mean()) / (clip.std() + 1e-6)
    return torch.from_numpy(clip).unsqueeze(0)


def predict(model, clip):
    model.eval()
    with torch.no_grad():
        p = torch.softmax(model(prep(clip).unsqueeze(0)), dim=1)[0]
    i = int(p.argmax())
    return i, float(p[i])


def model_path(lang):
    return os.path.join(MODEL_DIR, f"lip_{lang}.pt")


def save_model(lang, model, labels):
    os.makedirs(MODEL_DIR, exist_ok=True)
    torch.save({"labels": labels, "state": model.state_dict()}, model_path(lang))


def load_model(lang):
    p = model_path(lang)
    if not os.path.exists(p):
        return None
    try:
        d = torch.load(p, map_location="cpu")
        m = LipNet(len(d["labels"]))
        m.load_state_dict(d["state"])
        m.eval()
        return m, d["labels"]
    except Exception as e:  # noqa
        print("Gagal memuat model:", e)
        return None