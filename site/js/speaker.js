// Spoken warnings and messages through the browser's speechSynthesis, with
// the queue rules of Farid's Speaker (services.py), plus warning beeps.
// Browser-free: the synth, the utterance class and the clock are passed in.

const LANG_CODE = { id: "id-ID", en: "en-US" };
const langCode = (lang) => LANG_CODE[lang] || LANG_CODE.id;

// The best installed voice for "id" or "en", or null (the browser then picks
// one for utterance.lang by itself). Android reports Indonesian as "in".
export function pickVoice(voices, lang) {
  const want = langCode(lang).toLowerCase();
  const prefixes = lang === "en" ? ["en"] : ["id", "in"];
  const norm = (v) => String(v.lang || "").replace(/_/g, "-").toLowerCase();
  const exact = voices.find((v) => norm(v) === want);
  if (exact) return exact;
  const near = voices.find((v) => {
    const l = norm(v);
    return prefixes.some((p) => l === p || l.startsWith(p + "-"));
  });
  return near || null;
}

export class Speaker {
  constructor({ synth, Utterance, now = () => performance.now() / 1000, maxAge = 6 }) {
    this.synth = synth;
    this.Utterance = Utterance;
    this.now = now;
    this.maxAge = maxAge;
    this.queue = [];
    this.current = null;
  }

  // interrupt: stop what is playing, forget the queue, speak this now.
  say(text, lang, { interrupt = false } = {}) {
    if (interrupt) this.cancel();
    this.queue.push({ text, lang, time: this.now() });
    if (!this.current) this.next();
  }

  cancel() {
    this.queue = [];
    this.current = null;
    this.synth.cancel();
  }

  next() {
    while (this.queue.length) {
      const item = this.queue.shift();
      if (this.now() - item.time > this.maxAge) continue;   // too old to matter
      const u = new this.Utterance(item.text);
      u.lang = langCode(item.lang);
      const voice = pickVoice(this.synth.getVoices(), item.lang);
      if (voice) u.voice = voice;
      // A cancelled utterance can still report its end; only the current one counts.
      u.onend = u.onerror = () => {
        if (this.current !== u) return;
        this.current = null;
        this.next();
      };
      this.current = u;
      this.synth.speak(u);
      return;
    }
    this.current = null;
  }
}

// Farid's beep: level+1 tones of 130 ms, 1800 Hz for danger, else 1000 Hz.
export function beepPattern(level) {
  const freq = level === 2 ? 1800 : 1000;
  return Array.from({ length: level + 1 }, (_, i) => ({ freq, start: i * 0.2, dur: 0.13 }));
}

// Browser only: plays beepPattern(level) on a Web Audio context.
export function playBeep(audioCtx, level) {
  const t0 = audioCtx.currentTime + 0.02;
  for (const { freq, start, dur } of beepPattern(level)) {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    const a = t0 + start, b = a + dur;
    gain.gain.setValueAtTime(0, a);
    gain.gain.linearRampToValueAtTime(0.3, a + 0.01);
    gain.gain.setValueAtTime(0.3, b - 0.02);
    gain.gain.linearRampToValueAtTime(0, b);
    osc.connect(gain).connect(audioCtx.destination);
    osc.start(a);
    osc.stop(b + 0.01);
  }
}
