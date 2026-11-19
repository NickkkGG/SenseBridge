"""services.py - suara keluar, pengenalan suara, deteksi hambatan, mesin bibir"""
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import wave
from collections import deque

import numpy as np

import lipcore as lc


# ============================ SUARA KELUAR ============================
def _tone_wav(freq, ms):
    """macOS: file WAV nada sinus (dibuat sekali di folder temp) untuk afplay,
    pengganti winsound.Beep yang hanya ada di Windows."""
    path = os.path.join(tempfile.gettempdir(), f"sensebridge_beep_{freq}_{ms}.wav")
    if not os.path.exists(path):
        rate = 22050
        t = np.arange(int(rate * ms / 1000)) / rate
        pcm = (np.sin(2 * np.pi * freq * t) * 0.6 * 32767).astype("<i2")
        tmp = f"{path}.{threading.get_ident()}"
        with wave.open(tmp, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(pcm.tobytes())
        os.replace(tmp, path)
    return path


class Speaker:
    # macOS: suara bawaan untuk perintah `say` (lihat _run_mac)
    MAC_VOICES = {"id": "Damayanti", "en": "Samantha"}

    def __init__(self):
        self.q = queue.Queue()
        threading.Thread(target=self._run, daemon=True).start()

    @staticmethod
    def _pick_voice(engine, lang):
        want = ("indonesia", "id-id", "id_id") if lang == "id" \
            else ("english", "en-us", "en_us", "en-gb")
        for v in engine.getProperty("voices"):
            s = f"{v.name} {v.id} {getattr(v, 'languages', '')}".lower()
            if any(k in s for k in want):
                return v.id
        return None

    def _run(self):
        if sys.platform == "darwin":
            return self._run_mac()
        try:
            import pyttsx3
            engine = pyttsx3.init()
        except Exception as e:  # noqa
            print("Text-to-speech tidak tersedia:", e)
            return
        while True:
            text, lang, t = self.q.get()
            if time.time() - t > 6:      # buang pesan yang sudah basi
                continue
            try:
                vid = self._pick_voice(engine, lang)
                if vid:
                    engine.setProperty("voice", vid)
                engine.say(text)
                engine.runAndWait()
            except Exception as e:  # noqa
                print("TTS error:", e)

    def _run_mac(self):
        """macOS: pakai perintah `say`. pyttsx3 (driver nsss) di thread ini langsung
        selesai sebelum suaranya habis, jadi kalimat berikutnya memotong kalimat
        sebelumnya, dan bahasa Inggris malah dapat suara novelty "Albert"."""
        while True:
            text, lang, t = self.q.get()
            if time.time() - t > 6:      # buang pesan yang sudah basi
                continue
            try:
                # "--" supaya teks yang diawali "-" tidak dibaca sebagai opsi;
                # kalau suaranya tidak terpasang, `say` memakai suara default
                subprocess.run(["say", "-v", self.MAC_VOICES[lang], "--", text])
            except Exception as e:  # noqa
                print("TTS error:", e)

    def say(self, text, lang, interrupt=False):
        if interrupt:
            try:
                while True:
                    self.q.get_nowait()
            except queue.Empty:
                pass
        self.q.put((text, lang, time.time()))

    def beep(self, level):
        threading.Thread(target=self._beep, args=(level,), daemon=True).start()

    @staticmethod
    def _beep(level):
        try:
            if sys.platform == "darwin":     # macOS tidak punya winsound
                for _ in range(level + 1):
                    subprocess.run(["afplay", _tone_wav(1800 if level == 2 else 1000, 130)])
                return
            import winsound
            for _ in range(level + 1):
                winsound.Beep(1800 if level == 2 else 1000, 130)
        except Exception:  # noqa
            pass


# ============================ SUARA MASUK ============================
class SpeechListener:
    # Mikrofon dibaca lewat sounddevice (PortAudio sudah ikut di paketnya, jadi
    # tidak perlu pyaudio/Homebrew) per blok 0,1 detik, 16 kHz mono 16-bit:
    # format yang dipakai _recognize.
    RATE, BLOCK = 16000, 1600
    CALIB_BLOCKS = 10        # 1 detik pertama: ukur bising ruangan
    PREROLL_BLOCKS = 3       # 0,3 detik sebelum suara mulai ikut dikirim
    PAUSE_BLOCKS = 8         # hening 0,8 detik = kalimat selesai
    MAX_BLOCKS = 150         # kalimat paling panjang 15 detik
    MIN_VOICED = 3           # bunyi kurang dari 0,3 detik tidak dikirim ke Google
    LOUD_DBFS = -12          # lebih keras dari ini = peringatan suara keras
    ALERT_BLOCKS = 30        # jeda 3 detik antar peringatan (sama dengan banner)
    NO_AUDIO_BLOCKS = 20     # 2 detik nol digital = izin mikrofon belum ada

    def __init__(self, emit, get_lang):
        self.emit, self.get_lang = emit, get_lang
        self._stop = None

    def start(self):
        if self._stop is not None:
            self._stop.set()
        self._stop = threading.Event()
        threading.Thread(target=self._run, args=(self._stop,), daemon=True).start()

    def stop(self):
        if self._stop is not None:
            self._stop.set()

    def _run(self, stop):
        try:
            import sounddevice as sd
            import speech_recognition as sr
            rec = sr.Recognizer()
            with sd.InputStream(samplerate=self.RATE, blocksize=self.BLOCK,
                                channels=1, dtype="int16") as stream:
                self._listen(stream, stop, sr, rec)
        except Exception as e:  # noqa
            self.emit("stt_error", f"mic:{e}")

    def _listen(self, stream, stop, sr, rec):
        calib, zeros, noise = [], 0, None
        before = deque(maxlen=self.PREROLL_BLOCKS)
        phrase, voiced, quiet, cooldown = [], 0, 0, 0
        while not stop.is_set():
            block, _ = stream.read(self.BLOCK)
            if stop.is_set():                    # stop ditekan saat read() menunggu
                break
            rms = float(np.sqrt(np.mean(block.astype(np.float32) ** 2)))

            if noise is None:                    # --- kalibrasi bising ruangan
                if rms == 0:                     # nol digital: izin mikrofon belum ada
                    zeros += 1
                    if zeros == self.NO_AUDIO_BLOCKS:
                        self.emit("stt_error", "mic:" + (
                            "tidak ada suara masuk, cek izin mikrofon"
                            if self.get_lang() == "id"
                            else "no audio coming in, check the microphone permission"))
                    continue
                calib.append(rms)
                if len(calib) == self.CALIB_BLOCKS:
                    noise = float(np.median(calib))
                    self.emit("mic", "ready")
                continue

            dbfs = 20 * np.log10(max(rms, 1.0) / 32768)
            self.emit("level", min(1.0, max(0.0, (dbfs + 60) / 60)))
            cooldown = max(0, cooldown - 1)
            if dbfs > self.LOUD_DBFS and cooldown == 0:
                self.emit("alert", round(float(dbfs), 1))
                cooldown = self.ALERT_BLOCKS

            speaking = rms > max(noise * 3, 300)
            if phrase:                           # --- sedang merekam satu kalimat
                phrase.append(block)
                voiced, quiet = (voiced + 1, 0) if speaking else (voiced, quiet + 1)
                if quiet >= self.PAUSE_BLOCKS or len(phrase) >= self.MAX_BLOCKS:
                    if voiced >= self.MIN_VOICED:
                        raw = np.concatenate(phrase).tobytes()
                        threading.Thread(target=self._recognize, daemon=True,
                                         args=(sr, rec, raw, self.get_lang())).start()
                    phrase, voiced, quiet = [], 0, 0
            elif speaking:                       # --- kalimat baru dimulai
                phrase, voiced, quiet = list(before) + [block], 1, 0
            else:                                # --- hening: ikuti bising ruangan
                before.append(block)
                noise = 0.95 * noise + 0.05 * rms

    def _recognize(self, sr, rec, raw, lang):
        try:
            audio = sr.AudioData(raw, 16000, 2)
            text = rec.recognize_google(
                audio, language="id-ID" if lang == "id" else "en-US").strip()
            if text:
                self.emit("speech", text[0].upper() + text[1:])
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            self.emit("stt_error", "net")
        except Exception as e:  # noqa
            self.emit("stt_error", f"mic:{e}")


# ============================ DETEKSI HAMBATAN ============================
NAMES_ID = {
    "person": "orang", "chair": "kursi", "couch": "sofa", "bed": "tempat tidur",
    "dining table": "meja", "car": "mobil", "motorcycle": "motor",
    "bicycle": "sepeda", "bus": "bus", "truck": "truk", "dog": "anjing",
    "cat": "kucing", "bench": "bangku", "potted plant": "tanaman",
    "tv": "televisi", "laptop": "laptop", "bottle": "botol", "backpack": "tas",
    "suitcase": "koper", "toilet": "toilet", "refrigerator": "kulkas",
    "fire hydrant": "hidran", "stop sign": "rambu berhenti",
}
DIR = {"id": {"left": "kiri", "center": "depan", "right": "kanan"},
       "en": {"left": "on the left", "center": "ahead", "right": "on the right"}}


class ObstacleDetector:
    def __init__(self):
        self.model, self.ready, self.error = None, False, None
        self.result = ([], 0.0)
        self._busy, self._loading = False, False

    def start(self):
        if self.ready or self._loading:
            return
        self.error, self._loading = None, True
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO("yolov8n.pt")     # diunduh otomatis saat pertama kali
            self.ready = True
        except ImportError:
            self.error = "ultralytics"
        except Exception as e:  # noqa
            self.error = str(e)
        self._loading = False

    def submit(self, frame):
        if self._busy or not self.ready:
            return
        self._busy = True
        threading.Thread(target=self._infer, args=(frame,), daemon=True).start()

    def _infer(self, frame):
        try:
            r = self.model(frame, verbose=False, conf=0.4, imgsz=480)[0]
            out = []
            for b in r.boxes:
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                out.append((r.names[int(b.cls[0])], float(b.conf[0]),
                            x1, y1, x2, y2))
            self.result = (out, time.time())
        except Exception as e:  # noqa
            print("Deteksi error:", e)
        self._busy = False


def assess(dets, W, H, lang, sens=1.0):
    """Return (level 0/1/2, teks peringatan, zona, deteksi)."""
    best = None
    for d in dets:
        hr = (d[5] - d[3]) / H * sens
        if hr >= 0.40 and (best is None or hr > best[0]):
            best = (hr, d)
    if not best:
        return 0, "", "center", None
    hr, d = best
    lvl = 2 if hr >= 0.65 else 1
    cx = (d[2] + d[4]) / 2
    zone = "left" if cx < W / 3 else "right" if cx > 2 * W / 3 else "center"
    name = NAMES_ID.get(d[0], d[0]) if lang == "id" else d[0]
    where = DIR[lang][zone]
    if lang == "id":
        text = f"Awas! {name} sangat dekat di {where}" if lvl == 2 \
            else f"Hati-hati, ada {name} di {where}"
    else:
        text = f"Watch out! {name} very close {where}" if lvl == 2 \
            else f"Careful, {name} {where}"
    return lvl, text, zone, d


def mouth_open_ratio(lm, W, H):
    up, lo, l, r = lm[13], lm[14], lm[61], lm[291]
    gap = abs(lo.y - up.y) * H
    width = (((r.x - l.x) * W) ** 2 + ((r.y - l.y) * H) ** 2) ** 0.5
    return gap / max(width, 1e-6)


# ============================ MESIN BIBIR ============================
class LipEngine:
    def __init__(self):
        self.model, self.labels = None, []
        self.buf = deque(maxlen=lc.SEQ_LEN)
        self.n, self.last = 0, None

    def load(self, lang):
        r = lc.load_model(lang)
        self.model, self.labels = r if r else (None, [])
        self.reset()

    def reset(self):
        self.buf.clear()
        self.n, self.last = 0, None

    def push(self, roi):
        self.buf.append(roi)

    def step(self, thr):
        """Return (kata, keyakinan, baru) atau None."""
        if self.model is None or len(self.buf) < lc.SEQ_LEN:
            return None
        self.n += 1
        if self.n % 6:
            return None
        i, conf = lc.predict(self.model, np.stack(self.buf))
        word = self.labels[i]
        if word == lc.SILENCE or conf < thr:
            self.last = None
            return word, conf, False
        new = word != self.last
        self.last = word
        return word, conf, new