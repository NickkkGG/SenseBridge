// Line 2, Tuna Rungu: speech becomes large live captions with a timed
// history, and a loud sound flashes a banner (port of Farid's DeafPage).
import { basePage, applyText, h } from "../ui.js";
import { CaptionController, getRecognitionCtor } from "../captions.js";
import { openMic, stopStream, mediaErrorKey, keepScreenOn } from "../media.js";
import { rms, dbfs, levelFromDbfs, LoudAlert, meterTiming } from "../level.js";

const SEGMENTS = 24;
const HOT_FROM = Math.ceil(levelFromDbfs(-12) * SEGMENTS);   // segments above the loud threshold
const BANNER_MS = 3000;
const HISTORY_MAX = 100;

export function createPage(ctx) {
  const { el, body } = basePage({ line: "rungu", num: 2, titleKey: "rungu_title", subKey: "rungu_sub" });
  body.classList.add("rungu-grid");
  const band = h("div", { class: "alert-band", role: "alert", hidden: true });
  el.insertBefore(band, body);

  const go = h("button", { class: "go", type: "button" });
  const finalEl = h("span");
  const interimEl = h("span", { class: "interim" });
  const live = h("p", { class: "live" }, finalEl, interimEl);
  const segs = Array.from({ length: SEGMENTS }, (_, i) => h("i", { class: i >= HOT_FROM ? "hot" : null }));
  const meter = h("div", { class: "meter", "aria-hidden": "true", "data-level": "0.00" }, segs);
  const status = h("p", { class: "status", role: "status" });
  // Screen readers hear each finished sentence once, through the history.
  const history = h("ol", { class: "history", "aria-live": "polite", "aria-relevant": "additions" });

  body.append(
    go,
    h("div", { class: "rungu-live" },
      h("div", { class: "caption-board" }, h("p", { class: "label", "data-t": "live_caption" }), live, meter),
      status),
    h("div", { class: "rungu-side" },
      h("h2", { class: "label", "data-t": "history" }),
      history,
      h("p", { class: "note", "data-t": "rungu_note" })),
  );

  let run = 0;                 // bumps on every start and stop; stale callbacks check it
  let on = false;
  let captions = null, mic = null, micPending = false, audio = null, sampler = 0, bandTimer = 0, wake = null;
  let meterOff = false;        // the meter gave its microphone to captions
  let captionError = null;     // recognition refused before the microphone answered
  let liveFinal = "", interim = "", statusKey = null, sticky = false;
  const loud = new LoudAlert();

  function renderLive() {
    finalEl.textContent = liveFinal || (interim ? "" : ctx.t("waiting"));
    interimEl.textContent = interim ? (liveFinal ? " " : "") + interim : "";
  }

  function setStatus(key, bad = false) {
    statusKey = key;
    status.textContent = key ? ctx.t(key) : "";
    status.classList.toggle("bad", bad);
  }
  // A note stays until Stop; "listening" and the network message come and go
  // with every recognition restart and must not hide it.
  function note(key, bad = false) {
    sticky = true;
    setStatus(key, bad);
  }
  function passing(key, bad = false) {
    if (!sticky) setStatus(key, bad);
  }

  function renderButton() {
    go.textContent = ctx.t(on ? "stop" : "mic_on");
    go.classList.toggle("stop", on);
  }

  function addHistory(text) {
    const now = new Date();
    history.append(h("li", {},
      h("time", { datetime: now.toISOString() }, now.toTimeString().slice(0, 8)),
      h("span", {}, text)));
    while (history.children.length > HISTORY_MAX) history.firstElementChild.remove();
  }

  function setLevel(level) {
    const lit = Math.round(level * SEGMENTS);
    segs.forEach((s, i) => s.classList.toggle("on", i < lit));
    meter.dataset.level = level.toFixed(2);
  }

  function flashBand() {
    band.textContent = ctx.t("loud_alert");
    band.hidden = false;
    band.classList.remove("flash");
    void band.offsetWidth;          // restart the flash animation
    band.classList.add("flash");
    clearTimeout(bandTimer);
    bandTimer = setTimeout(() => {
      band.hidden = true;
      band.classList.remove("flash");
    }, BANNER_MS);
  }

  // Level meter and loud-sound alert on their own microphone stream.
  function startMeter(stream) {
    const { fftSize, intervalMs } = meterTiming(audio.sampleRate);
    const analyser = audio.createAnalyser();
    analyser.fftSize = fftSize;
    audio.createMediaStreamSource(stream).connect(analyser);
    const buf = new Float32Array(fftSize);
    sampler = setInterval(() => {
      analyser.getFloatTimeDomainData(buf);
      const d = dbfs(rms(buf));
      setLevel(levelFromDbfs(d));
      if (loud.check(d, performance.now() / 1000)) flashBand();
    }, intervalMs);
  }

  function releaseMeter() {
    clearInterval(sampler);
    sampler = 0;
    stopStream(mic);
    mic = null;
    audio?.close().catch(() => {});
    audio = null;
    setLevel(0);
  }

  function startCaptions(my) {
    const guard = (fn) => (...args) => { if (my === run) fn(...args); };
    let fatal = null;
    captions = new CaptionController({
      Recognition: getRecognitionCtor(window),
      lang: ctx.lang(),
      onInterim: guard((text) => { interim = text; renderLive(); }),
      onFinal: guard((text) => { liveFinal = text; interim = ""; renderLive(); addHistory(text); }),
      onError: guard((key) => {
        if (key === "err_net") passing(key, true);
        else fatal = key;
      }),
      onStatus: guard((s) => {
        if (s === "listening") passing("listening");
        else if (s === "stopped") captionsStopped(my, fatal);
      }),
    });
    captions.start();
  }

  // Captions ended for good (permission, no microphone, language).
  function captionsStopped(my, key) {
    captions = null;
    if (key === "no_mic" && !meterOff && (mic || micPending)) {
      // On some phones the meter's own microphone stream locks the recognizer
      // out: give the microphone to captions, once.
      meterOff = true;
      releaseMeter();
      note("meter_off");
      startCaptions(my);
    } else if (key === "perm_mic" && micPending) {
      captionError = key;              // decided when the microphone answers
    } else if (key === "perm_mic" && mic) {
      note("speech_denied", true);     // the microphone works; only recognition was refused
    } else if (mic) {
      note(key, true);                 // the meter and the loud alert keep running
    } else {
      stop();
      setStatus(key, true);
    }
  }

  async function start() {
    const my = ++run;
    on = true;
    meterOff = false;
    captionError = null;
    sticky = false;
    renderButton();
    setStatus(null);
    interim = "";
    renderLive();
    wake = keepScreenOn(navigator, document);

    // Made inside the tap, so the browser lets it run.
    const AC = window.AudioContext || window.webkitAudioContext;
    audio = AC ? new AC() : null;
    audio?.resume().catch(() => {});

    if (getRecognitionCtor(window)) startCaptions(my);
    else note("no_speech_api", true);      // Firefox: the loud-sound alert still runs

    micPending = true;
    let stream;
    try {
      stream = await openMic();
    } catch (err) {
      if (my !== run) return;
      micPending = false;
      const key = mediaErrorKey(err, "mic");
      // Captions have their own access to the microphone: keep them when only
      // the level meter could not get it.
      if (captions && (key === "mic_busy" || key === "mic_error")) {
        releaseMeter();
        note(key, true);
        return;
      }
      stop();
      setStatus(key, true);
      return;
    }
    if (my !== run) {
      stopStream(stream);
      return;
    }
    micPending = false;
    if (meterOff || !audio) {
      stopStream(stream);
    } else {
      mic = stream;
      startMeter(stream);
    }
    if (captionError) {                    // recognition was refused while the mic was asked
      const key = captionError;
      captionError = null;
      if (mic) {
        note("speech_denied", true);
      } else {
        stop();
        setStatus(key, true);
      }
    }
  }

  // Ends captions, the level meter and every microphone track. The last
  // caption and the history stay on screen.
  function stop() {
    run++;
    on = false;
    captions?.stop();
    captions = null;
    releaseMeter();
    wake?.release();
    wake = null;
    micPending = false;
    meterOff = false;
    captionError = null;
    sticky = false;
    clearTimeout(bandTimer);
    band.hidden = true;
    band.classList.remove("flash");
    interim = "";
    renderLive();
    setStatus(null);
    renderButton();
  }

  go.addEventListener("click", () => (on ? stop() : start()));

  function setLang(lang) {
    applyText(el, ctx.t);
    renderButton();
    renderLive();
    if (statusKey) status.textContent = ctx.t(statusKey);
    if (!band.hidden) band.textContent = ctx.t("loud_alert");
    captions?.setLang(lang);
  }

  setLang(ctx.lang());
  return {
    el,
    show() {},
    hide() {
      if (on) stop();
    },
    setLang,
  };
}
