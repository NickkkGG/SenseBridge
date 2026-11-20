// Live captions through the browser's own speech recognition (Web Speech
// API). Browser-free: the recognizer class and the timer are passed in.

const LANG_CODE = { id: "id-ID", en: "en-US" };

// Errors that end captions until the user presses Start again.
const FATAL = {
  "not-allowed": "perm_mic",
  "service-not-allowed": "perm_mic",
  "audio-capture": "no_mic",
  "language-not-supported": "lang_unsupported",
};

// Chrome, Edge and Safari have it (Chrome and Safari with the webkit prefix);
// Firefox does not.
export function getRecognitionCtor(win) {
  return win.SpeechRecognition || win.webkitSpeechRecognition || null;
}

export class CaptionController {
  constructor({ Recognition, lang, onInterim = () => {}, onFinal = () => {},
    onError = () => {}, onStatus = () => {}, schedule = setTimeout }) {
    Object.assign(this, { Recognition, lang, onInterim, onFinal, onError, onStatus, schedule });
    this.active = false;
    this.rec = null;
    this.retryDelay = 0;
  }

  start() {
    if (this.active) return;
    this.active = true;
    this.retryDelay = 0;
    this.rec = this.create();
    this.begin(this.rec);
  }

  stop() {
    this.active = false;
    if (this.rec) this.rec.stop();
  }

  setLang(lang) {
    this.lang = lang;
    if (!this.active) return;
    const old = this.rec;
    this.rec = this.create();       // the old one's events are ignored from now on
    if (old) old.abort();
    this.begin(this.rec);
  }

  begin(rec) {
    try {
      rec.start();
    } catch {
      // Already started: nothing to do.
    }
  }

  create() {
    const rec = new this.Recognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = LANG_CODE[this.lang] || LANG_CODE.id;
    const current = () => this.rec === rec;

    rec.onstart = () => {
      if (current()) this.onStatus("listening");
    };
    rec.onresult = (e) => {
      if (!current()) return;
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        const text = res[0].transcript;
        if (res.isFinal) {
          const clean = text.trim();
          if (clean) this.onFinal(clean[0].toUpperCase() + clean.slice(1));
        } else {
          interim += text;
        }
      }
      if (interim) this.onInterim(interim);
    };
    rec.onerror = (e) => {
      if (!current()) return;
      const err = e.error;
      if (err === "no-speech" || err === "aborted") return;
      if (Object.hasOwn(FATAL, err)) {
        this.active = false;
        this.onError(FATAL[err]);
        this.onStatus("stopped");
        return;
      }
      if (err === "network") this.onError("err_net");
      this.retryDelay = 1000;       // network and unknown errors: retry, but not in a tight loop
    };
    rec.onend = () => {
      if (!current() || !this.active) return;
      const wait = this.retryDelay;
      this.retryDelay = 0;
      const schedule = this.schedule;   // unbound: the browser's setTimeout refuses another `this`
      schedule(() => {
        if (current() && this.active) this.begin(rec);
      }, wait);
    };
    return rec;
  }
}
