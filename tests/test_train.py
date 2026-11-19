"""Tes train.py: melatih LipNet dari klip buatan lalu memakai modelnya.

"Mulut" dibuat dari elips gelap yang membuka-menutup dengan pola berbeda per
kata, jadi model harus belajar dari gerakannya, bukan dari satu frame saja.

Jalankan dari folder project:  .venv/bin/python -m unittest discover tests
"""
import os
import sys
import tempfile
import unittest

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import lipcore as lc  # noqa: E402

YY, XX = np.mgrid[0:lc.IMG, 0:lc.IMG]

# tinggi bukaan mulut (0..1) sepanjang klip, t = 0..1
PATTERNS = {
    "_diam": lambda t: np.zeros_like(t),                # diam terus
    "halo": lambda t: np.abs(np.sin(2 * np.pi * t)),    # membuka dua kali
    "tolong": lambda t: np.sin(np.pi * t),              # membuka sekali, pelan
}


def mouth_clip(pattern, rng):
    """Satu klip (24, 48, 48) uint8 seperti hasil rekam halaman Latih Model."""
    speed, amp = rng.uniform(0.85, 1.15), rng.uniform(0.7, 1.0)
    t = np.clip(np.linspace(0, 1, lc.SEQ_LEN) * speed - (speed - 1) / 2, 0, 1)
    dy, dx = rng.integers(-2, 3, size=2)
    frames = []
    for opening in amp * pattern(t):
        img = np.full((lc.IMG, lc.IMG), 170.0)                     # kulit
        inside = ((XX - 24 - dx) / 14.0) ** 2 + ((YY - 24 - dy) / (2 + 12 * opening)) ** 2 <= 1
        img[inside] = 60                                          # rongga mulut
        img += rng.normal(0, 8, img.shape)
        frames.append(np.clip(img, 0, 255).astype(np.uint8))
    return np.stack(frames)


class TrainTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.saved_dirs = lc.DATA_DIR, lc.MODEL_DIR
        lc.DATA_DIR = os.path.join(self.tmp.name, "dataset")
        lc.MODEL_DIR = os.path.join(self.tmp.name, "models")
        self.logs = []

    def tearDown(self):
        lc.DATA_DIR, lc.MODEL_DIR = self.saved_dirs
        self.tmp.cleanup()

    def record(self, word, n, seed, pattern=None):
        rng = np.random.default_rng(seed)
        folder = os.path.join(lc.DATA_DIR, "id", word)
        os.makedirs(folder, exist_ok=True)
        for i in range(n):
            np.save(os.path.join(folder, f"{i}.npy"),
                    mouth_clip(pattern or PATTERNS[word], rng))

    def test_trained_model_reads_new_clips_of_each_word(self):
        import train
        for seed, word in enumerate(PATTERNS):
            self.record(word, 16, seed)
        self.record("ya", 2, 9, pattern=PATTERNS["halo"])     # terlalu sedikit: dilewati

        msg = train.train("id", epochs=20, log=self.logs.append)

        self.assertFalse(msg.startswith("Error"), msg)
        self.assertTrue(self.logs, "tidak ada log progres")
        loaded = lc.load_model("id")
        self.assertIsNotNone(loaded, "model tidak tersimpan")
        model, labels = loaded
        self.assertEqual(labels, ["_diam", "halo", "tolong"])
        rng = np.random.default_rng(1234)                     # klip baru, belum pernah dilihat
        results = [(word, labels[lc.predict(model, mouth_clip(pattern, rng))[0]])
                   for word, pattern in PATTERNS.items() for _ in range(8)]
        correct = sum(want == got for want, got in results)
        self.assertGreaterEqual(correct / len(results), 0.9, results)

    def test_too_little_data_returns_an_error_and_saves_nothing(self):
        import train
        for setup in ("no recordings", "only one word"):
            with self.subTest(setup):
                if setup == "only one word":
                    self.record("halo", 10, 0)
                msg = train.train("id", epochs=2, log=self.logs.append)
                self.assertTrue(msg.startswith("Error"), msg)
                self.assertIsNone(lc.load_model("id"))


if __name__ == "__main__":
    unittest.main()
