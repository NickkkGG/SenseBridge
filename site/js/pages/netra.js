// Line 1, Tuna Netra: the camera looks ahead; close obstacles become a big
// status board, spoken warnings and beeps (port of Farid's BlindPage).
import { basePage, applyText, h, switchButton } from "../ui.js";
import { openCamera, shouldMirror, stopStream, mediaErrorKey, keepScreenOn } from "../media.js";
import { assess, heightLevel, AlertGate, fromMediaPipe } from "../obstacles.js";
import { NAMES_ID } from "../i18n.js";
import { createObjectDetector } from "../vision.js";

const LEVELS = ["safe", "caution", "danger"];
const LEVEL_KEYS = ["lvl_safe", "lvl_caution", "lvl_danger"];
const ZONES = ["left", "center", "right"];
const DETECT_EVERY_MS = 66;          // at most about 15 detections a second
const FAR = "#A3A9B8";               // boxes too far away to warn about

export function createPage(ctx) {
  const { el, body } = basePage({ line: "netra", num: 1, titleKey: "netra_title", subKey: "netra_sub" });
  body.classList.add("netra-grid");

  // Status board. It is a live region only while voice warnings are off, so
  // a screen reader and the spoken warnings do not talk over each other.
  const levelEl = h("p", { class: "level", hidden: true });
  const msgEl = h("p", { class: "msg" });
  const board = h("div", { class: "board", "aria-live": "off", "aria-atomic": "true" }, levelEl, msgEl);

  const go = h("button", { class: "go", type: "button" });
  const status = h("p", { class: "status bad", role: "alert" });

  const idle = h("div", { class: "idle", "aria-hidden": "true", "data-t": "idle" });
  const video = h("video", { "aria-hidden": "true", hidden: true });
  const canvas = h("canvas", { "aria-hidden": "true", hidden: true });
  const viewer = h("div", { class: "viewer" }, idle, video, canvas);
  const zoneEls = ZONES.map((z) => h("span", { class: "zone", "data-t": `zone_${z}` }));

  let voiceOn = true, beepOn = true, sens = 1;
  const voiceSwitch = switchButton("voice_warn", true, (on) => {
    voiceOn = on;
    board.setAttribute("aria-live", on ? "off" : "polite");
    if (!on) ctx.speaker.cancel();
  });
  const beepSwitch = switchButton("beep", true, (on) => { beepOn = on; });
  const sensOut = h("output", {}, "1.0");
  const sensRange = h("input", { type: "range", min: "0.6", max: "1.6", step: "0.1", value: "1" });
  sensRange.addEventListener("input", () => {
    sens = Number(sensRange.value);
    sensOut.textContent = sens.toFixed(1);
  });

  body.append(
    board,
    h("div", { class: "go-wrap" }, go, status),
    h("div", { class: "netra-view" }, viewer, h("div", { class: "zones", "aria-hidden": "true" }, zoneEls)),
    h("div", { class: "netra-more" },
      h("div", { class: "opts" },
        h("div", { class: "opt" }, voiceSwitch),
        h("div", { class: "opt" }, beepSwitch),
        h("label", { class: "range" }, h("span", { class: "range-top" }, h("span", { "data-t": "sens" }), sensOut), sensRange)),
      h("p", { class: "note", "data-t": "disclaimer" })),
  );

  let run = 0;                 // bumps on every start and stop; stale async work checks it
  let running = false;         // between Start and Stop (the camera may still be opening)
  let stream = null, raf = 0, lastDetect = 0, mirror = false, gate = new AlertGate();
  let idleKey = "idle", errorKey = null, shown = "", colors = null;
  let detectorLoaded = false, wake = null;

  function setBoard(level, text) {
    const key = `${level}|${text}`;
    if (key === shown) return;        // unchanged: keep live regions quiet
    shown = key;
    board.className = level >= 0 ? `board ${LEVELS[level]}` : "board";
    levelEl.hidden = level < 0;
    levelEl.textContent = level >= 0 ? ctx.t(LEVEL_KEYS[level]) : "";
    msgEl.textContent = text;
  }

  function setZones(level, zone) {
    zoneEls.forEach((z, i) => {
      const on = level > 0 && ZONES[i] === zone;
      z.classList.toggle("on", on);
      z.style.setProperty("--sig", on ? (level === 2 ? "var(--bad)" : "var(--warn)") : "");
    });
  }

  function showIdle(key) {
    idleKey = key;
    setBoard(-1, ctx.t(key));
    setZones(0, "center");
  }

  function setError(key) {
    errorKey = key;
    status.textContent = key ? ctx.t(key) : "";
    if (key && voiceOn) ctx.speaker.say(ctx.t(key), ctx.lang(), { interrupt: true });
  }

  function renderButton() {
    go.textContent = ctx.t(running ? "stop" : "start");
    go.classList.toggle("stop", running);
  }

  function draw(dets, picked, W, H) {
    if (canvas.width !== W) canvas.width = W;
    if (canvas.height !== H) canvas.height = H;
    const g = canvas.getContext("2d");
    g.clearRect(0, 0, W, H);
    if (!colors) {
      const css = getComputedStyle(el);
      colors = [FAR, css.getPropertyValue("--warn").trim(), css.getPropertyValue("--bad").trim(),
        css.getPropertyValue("--on-signal").trim()];
    }
    const size = Math.round(Math.max(14, W / 34));
    const lw = Math.max(2, W / 220);
    g.font = `600 ${size}px "Atkinson Hyperlegible Mono", ui-monospace, monospace`;
    g.textBaseline = "top";
    for (const d of dets) {
      const color = colors[heightLevel(d, H, sens)];
      g.lineWidth = d === picked ? lw * 1.8 : lw;
      g.strokeStyle = color;
      g.strokeRect(d.x1, d.y1, d.x2 - d.x1, d.y2 - d.y1);
      const name = ctx.lang() === "id" && Object.hasOwn(NAMES_ID, d.name) ? NAMES_ID[d.name] : d.name;
      const pad = size * 0.3;
      g.fillStyle = color;
      g.fillRect(d.x1, d.y1, g.measureText(name).width + pad * 2, size + pad * 1.4);
      g.fillStyle = colors[3];
      g.fillText(name, d.x1 + pad, d.y1 + pad * 0.7);
    }
  }

  function loop(my, detector) {
    const tick = (now) => {
      if (my !== run) return;
      raf = requestAnimationFrame(tick);
      if (now - lastDetect < DETECT_EVERY_MS || video.readyState < 2) return;
      lastDetect = now;
      let result;
      try {
        result = detector.detectForVideo(video, performance.now());
      } catch {
        stop();
        setError("model_failed");
        return;
      }
      const W = video.videoWidth, H = video.videoHeight;
      const dets = fromMediaPipe(result, W, mirror);
      const r = assess(dets, W, H, ctx.lang(), sens);
      draw(dets, r.det, W, H);
      setBoard(r.level, r.level === 0 ? ctx.t("path_clear") : r.text);
      setZones(r.level, r.zone);
      if (gate.shouldAlert(r.level, r.text, now / 1000)) {
        if (voiceOn) ctx.speaker.say(r.text, ctx.lang(), { interrupt: r.level === 2 });
        if (beepOn) ctx.beep(r.level);
      }
    };
    raf = requestAnimationFrame(tick);
  }

  async function start() {
    const my = ++run;
    running = true;
    renderButton();
    setError(null);
    ctx.unlockAudio();
    wake = keepScreenOn(navigator, document);

    let s;
    try {
      s = await openCamera(video, "environment");
    } catch (err) {
      if (my !== run) return;
      stop();
      setError(mediaErrorKey(err, "camera"));
      return;
    }
    if (my !== run) {
      stopStream(s);
      return;
    }
    stream = s;
    mirror = shouldMirror(s.getVideoTracks()[0]);
    video.classList.toggle("mirror", mirror);
    viewer.classList.toggle("portrait", video.videoHeight > video.videoWidth);
    idle.hidden = true;
    video.hidden = false;
    canvas.hidden = false;
    showIdle("loading_model");
    // The first load downloads about 18 MB: say so, or silence would sound like a clear path.
    if (voiceOn && !detectorLoaded) ctx.speaker.say(ctx.t("loading_model"), ctx.lang());

    let detector;
    try {
      detector = await createObjectDetector();
    } catch {
      if (my !== run) return;
      stop();
      setError("model_failed");
      return;
    }
    detectorLoaded = true;
    if (my !== run) return;
    gate = new AlertGate();
    lastDetect = 0;
    if (voiceOn) ctx.speaker.say(ctx.t("netra_started"), ctx.lang());
    loop(my, detector);
  }

  // Ends the loop and every camera track, and puts the page back to idle.
  function stop() {
    run++;
    running = false;
    cancelAnimationFrame(raf);
    wake?.release();
    wake = null;
    stopStream(stream);
    stream = null;
    video.srcObject = null;
    video.hidden = true;
    canvas.hidden = true;
    idle.hidden = false;
    canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
    showIdle("idle");
    renderButton();
  }

  go.addEventListener("click", () => {
    if (running) {
      stop();
      ctx.speaker.cancel();
    } else {
      start();
    }
  });

  function setLang() {
    applyText(el, ctx.t);
    renderButton();
    if (errorKey) status.textContent = ctx.t(errorKey);
    const idleShown = shown.startsWith("-1|");
    shown = "";
    if (idleShown) setBoard(-1, ctx.t(idleKey));   // a running board refreshes on the next detection
  }

  setLang();
  showIdle("idle");
  return {
    el,
    show() {},
    hide() {
      if (running) stop();
    },
    setLang,
  };
}
