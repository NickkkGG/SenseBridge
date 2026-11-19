"""Tes SpeechListener (mikrofon halaman Tuna Rungu) tanpa mikrofon dan tanpa internet.

Mikrofon diganti stream palsu yang memutar sinyal buatan blok per blok, dan
Google Speech diganti fungsi palsu, jadi yang dites hanya logika SpeechListener.

Jalankan dari folder project:  .venv/bin/python -m unittest discover tests
"""
import os
import sys
import time
import types
import unittest

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import services  # noqa: E402
import speech_recognition as sr  # noqa: E402

RATE = 16000
rng = np.random.default_rng(7)


# ---- sinyal buatan: (label, sampel int16 pada 16 kHz) ----
def quiet(sec):
    """Ruangan sepi: RMS ~100 (sekitar -50 dBFS)."""
    return "quiet", rng.normal(0, 100, int(RATE * sec))


def voice(sec):
    """Mirip ucapan: nada 200/400/800 Hz, RMS ~1860 (sekitar -25 dBFS)."""
    t = np.arange(int(RATE * sec)) / RATE
    x = (2000 * np.sin(2 * np.pi * 200 * t) + 1500 * np.sin(2 * np.pi * 400 * t)
         + 800 * np.sin(2 * np.pi * 800 * t))
    return "voice", x + rng.normal(0, 100, len(t))


def bang(sec):
    """Benturan keras: RMS ~17300 (sekitar -5,5 dBFS)."""
    return "bang", rng.uniform(-30000, 30000, int(RATE * sec))


def silence(sec):
    """Nol digital: yang dikirim macOS kalau izin mikrofon belum diberikan."""
    return "zeros", np.zeros(int(RATE * sec))


class FakeInputStream:
    """Pengganti sounddevice.InputStream: memutar `script` seperti mikrofon."""
    script = []      # list (label, sampel), diisi oleh tiap tes
    fail = None      # exception yang dilempar saat stream dibuka
    last = None      # stream terakhir yang dibuat
    read_delay = 0.002   # mikrofon asli menahan read() 0,1 detik per blok

    def __init__(self, samplerate=None, blocksize=None, device=None, channels=None,
                 dtype=None, **kwargs):
        if FakeInputStream.fail is not None:
            raise FakeInputStream.fail
        self.samplerate, self.channels, self.dtype = samplerate, channels, dtype
        self.data = np.clip(np.concatenate([x for _, x in self.script]),
                            -32768, 32767).astype(np.int16)
        self.bounds, end = [], 0
        for label, x in self.script:
            end += len(x)
            self.bounds.append((end, label))
        self.pos, self.label, self.closed = 0, None, False
        FakeInputStream.last = self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True

    def read(self, frames):
        time.sleep(self.read_delay)
        self.label = next((lab for end, lab in self.bounds if self.pos < end), "after")
        chunk = self.data[self.pos:self.pos + frames]
        self.pos += frames
        if len(chunk) < frames:          # naskah habis: anggap ruangan sepi terus
            pad = rng.normal(0, 100, frames - len(chunk)).astype(np.int16)
            chunk = np.concatenate([chunk, pad])
        return chunk.reshape(-1, self.channels or 1), False


class SpeechListenerTest(unittest.TestCase):
    def setUp(self):
        self.real_sd = sys.modules.get("sounddevice")
        self.fake_sd = types.ModuleType("sounddevice")
        self.fake_sd.InputStream = FakeInputStream
        self.fake_sd.PortAudioError = type("PortAudioError", (Exception,), {})
        sys.modules["sounddevice"] = self.fake_sd
        FakeInputStream.fail, FakeInputStream.last = None, None
        FakeInputStream.read_delay = 0.002

        self.calls = []
        self.real_google = sr.Recognizer.recognize_google

        def fake_google(recognizer, audio_data, key=None, language="en-US", **kwargs):
            self.calls.append({
                "seconds": len(audio_data.frame_data)
                / (audio_data.sample_rate * audio_data.sample_width),
                "rate": audio_data.sample_rate, "width": audio_data.sample_width,
                "language": language})
            return "halo apa kabar"

        sr.Recognizer.recognize_google = fake_google
        self.events, self.lang = [], "id"
        self.listener = services.SpeechListener(self.record, lambda: self.lang)

    def tearDown(self):
        self.listener.stop()
        time.sleep(0.05)
        sr.Recognizer.recognize_google = self.real_google
        if self.real_sd is None:
            sys.modules.pop("sounddevice", None)
        else:
            sys.modules["sounddevice"] = self.real_sd

    # ---- alat bantu ----
    def record(self, kind, payload):
        stream = FakeInputStream.last
        self.events.append((kind, payload, stream.label if stream else None))

    def play(self, *segments):
        FakeInputStream.script = list(segments)
        self.listener.start()

    def wait_for(self, cond, timeout=5.0):
        end = time.time() + timeout
        while time.time() < end:
            if cond():
                return True
            time.sleep(0.02)
        return False

    def played_to_end(self):
        return self.wait_for(lambda: FakeInputStream.last is not None
                             and FakeInputStream.last.label == "after")

    def of(self, kind):
        return [e for e in self.events if e[0] == kind]

    def summary(self):
        return [e[:2] for e in self.events if e[0] != "level"]

    # ---- tes ----
    def test_two_phrases_with_a_pause_are_recognized_separately(self):
        self.play(quiet(1.5), voice(1.0), quiet(1.5), voice(0.6), quiet(1.5))
        self.assertTrue(self.played_to_end(), self.summary())
        self.assertTrue(self.wait_for(lambda: len(self.calls) >= 2), self.summary())
        time.sleep(0.2)                                  # pastikan tidak ada kalimat ketiga
        stream = FakeInputStream.last
        self.assertEqual((stream.samplerate, stream.channels, stream.dtype), (16000, 1, "int16"))
        self.assertEqual(len(self.calls), 2, self.calls)
        first, second = self.calls
        self.assertTrue(1.0 <= first["seconds"] < 2.5, first)      # utuh, tidak ikut kalimat ke-2
        self.assertTrue(0.6 <= second["seconds"] < 2.1, second)
        for call in self.calls:
            self.assertEqual((call["rate"], call["width"], call["language"]), (16000, 2, "id-ID"))
        self.assertEqual([e[1] for e in self.of("speech")], ["Halo apa kabar"] * 2)
        ready = [i for i, e in enumerate(self.events) if e[:2] == ("mic", "ready")]
        first_speech = next(i for i, e in enumerate(self.events) if e[0] == "speech")
        self.assertEqual(len(ready), 1)
        self.assertLess(ready[0], first_speech)

    def test_recognition_uses_the_current_language(self):
        self.lang = "en"
        self.play(quiet(1.5), voice(1.0), quiet(1.5))
        self.assertTrue(self.wait_for(lambda: self.calls), self.summary())
        self.assertEqual([c["language"] for c in self.calls], ["en-US"])

    def test_loud_sound_raises_one_alert_until_the_cooldown_ends(self):
        self.play(quiet(1.5), bang(0.5), quiet(4.0), bang(0.3), quiet(1.0))
        self.assertTrue(self.played_to_end(), self.summary())
        self.assertEqual([e[2] for e in self.of("alert")], ["bang", "bang"], self.summary())

    def test_level_rises_with_loudness_and_stays_between_0_and_1(self):
        self.play(quiet(2.5), voice(1.0), bang(0.5), silence(0.3), quiet(0.5))
        self.assertTrue(self.played_to_end(), self.summary())
        levels = {}
        for kind, payload, label in self.events:
            if kind == "level":
                levels.setdefault(label, []).append(payload)
        self.assertTrue(all(0.0 <= v <= 1.0 for vs in levels.values() for v in vs), levels)
        self.assertLess(max(levels["quiet"]), min(levels["voice"]))
        self.assertLess(max(levels["voice"]), min(levels["bang"]))
        self.assertEqual(set(levels["zeros"]), {0.0})

    def test_digital_silence_warns_then_listens_once_audio_arrives(self):
        self.play(silence(3.0), quiet(1.5), voice(1.0), quiet(1.5))
        self.assertTrue(self.wait_for(lambda: self.of("speech")), self.summary())
        errors = self.of("stt_error")
        self.assertEqual(len(errors), 1, self.summary())
        self.assertTrue(errors[0][1].startswith("mic:"), errors)
        self.assertEqual(errors[0][2], "zeros")
        ready = [e for e in self.events if e[:2] == ("mic", "ready")]
        self.assertEqual(len(ready), 1)
        self.assertNotEqual(ready[0][2], "zeros")
        self.assertLess(self.events.index(errors[0]), self.events.index(ready[0]))

    def test_microphone_that_cannot_open_reports_a_mic_error(self):
        FakeInputStream.fail = self.fake_sd.PortAudioError("Error querying device -1")
        self.listener.start()
        self.assertTrue(self.wait_for(lambda: self.events), "tidak ada event sama sekali")
        time.sleep(0.1)
        self.assertEqual([e[:2] for e in self.events],
                         [("stt_error", "mic:Error querying device -1")])

    def test_stop_closes_the_microphone(self):
        self.play(quiet(1.5))
        self.assertTrue(self.wait_for(lambda: self.of("mic")), self.summary())
        self.listener.stop()
        self.assertTrue(self.wait_for(lambda: FakeInputStream.last.closed, timeout=1.0))
        count = len(self.events)
        time.sleep(0.2)
        self.assertEqual(len(self.events), count)

    def test_block_being_read_when_stop_is_pressed_emits_nothing(self):
        FakeInputStream.read_delay = 0.1                 # tempo mikrofon asli
        self.play(quiet(3.0))
        self.assertTrue(self.wait_for(lambda: self.of("level")), self.summary())
        time.sleep(0.05)                                 # stop di tengah read()
        self.listener.stop()
        count = len(self.events)
        time.sleep(0.3)
        self.assertEqual(self.events[count:], [])


if __name__ == "__main__":
    unittest.main()
