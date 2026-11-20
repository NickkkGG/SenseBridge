// Line 2, Tuna Rungu: speech becomes large live captions with a timed
// history, and a loud sound flashes a banner (port of Farid's DeafPage).
import { basePage, applyText, h } from "../ui.js";
import { CaptionController, getRecognitionCtor } from "../captions.js";
import { openMic, stopStream, mediaErrorKey } from "../media.js";
import { rms, dbfs, levelFromDbfs, LoudAlert } from "../level.js";

const SEGMENTS = 24;
const HOT_FROM = Math.ceil(levelFromDbfs(-12) * SEGMENTS);   // segments above the loud threshold
const SAMPLE_MS = 100;
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
  let captions = null, mic = null, audio = null, sampler = 0, bandTimer = 0;
  let liveFinal = "", interim = "", statusKey = null;
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

  async function start() {
    const my = ++run;
    const guard = (fn) => (...args) => { if (my === run) fn(...args); };
    on = true;
    renderButton();
    setStatus(null);
    interim = "";
    renderLive();

    // Made inside the tap, so the browser lets it run.
    const AC = window.AudioContext || window.webkitAudioContext;
    audio = AC ? new AC() : null;
    audio?.resume().catch(() => {});

    const Recognition = getRecognitionCtor(window);
    if (Recognition) {
      captions = new CaptionController({
        Recognition,
        lang: ctx.lang(),
        onInterim: guard((text) => { interim = text; renderLive(); }),
        onFinal: guard((text) => { liveFinal = text; interim = ""; renderLive(); addHistory(text); }),
        onError: guard((key) => setStatus(key, true)),
        onStatus: guard((s) => { if (s === "listening") setStatus("listening"); }),
      });
      captions.start();
    } else {
      setStatus("no_speech_api", true);      // Firefox: the loud-sound alert still runs
    }

    let stream;
    try {
      stream = await openMic();
    } catch (err) {
      if (my !== run) return;
      const key = mediaErrorKey(err, "mic");
      // Captions have their own access to the microphone: keep them when only
      // the level meter could not get it.
      if (captions && (key === "mic_busy" || key === "mic_error")) {
        setStatus(key, true);
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
    mic = stream;
    if (!audio) return;
    const analyser = audio.createAnalyser();
    analyser.fftSize = 2048;
    audio.createMediaStreamSource(stream).connect(analyser);
    const buf = new Float32Array(analyser.fftSize);
    sampler = setInterval(() => {
      analyser.getFloatTimeDomainData(buf);
      const d = dbfs(rms(buf));
      setLevel(levelFromDbfs(d));
      if (loud.check(d, performance.now() / 1000)) flashBand();
    }, SAMPLE_MS);
  }

  // Ends captions, the level meter and every microphone track. The last
  // caption and the history stay on screen.
  function stop() {
    run++;
    on = false;
    captions?.stop();
    captions = null;
    clearInterval(sampler);
    sampler = 0;
    stopStream(mic);
    mic = null;
    audio?.close().catch(() => {});
    audio = null;
    clearTimeout(bandTimer);
    band.hidden = true;
    band.classList.remove("flash");
    interim = "";
    renderLive();
    setLevel(0);
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
