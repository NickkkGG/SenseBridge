// SenseBridge web app: settings, header controls and hash routing between
// the home line list and the four line pages.
import { t as translate } from "./i18n.js";
import { loadSettings, saveSetting } from "./settings.js";
import { Speaker, playBeep } from "./speaker.js";
import { applyText } from "./ui.js";
import { createPage as createNetra } from "./pages/netra.js";
import { createPage as createRungu } from "./pages/rungu.js";
import { createPage as createWicara } from "./pages/wicara.js";
import { createPage as createLatih } from "./pages/latih.js";

const root = document.documentElement;
const storage = (() => {
  try {
    return window.localStorage;
  } catch {
    return null;       // blocked site data: defaults, nothing saved
  }
})();
let lang = loadSettings(storage).lang;

// Voice and beeps ------------------------------------------------------------
const synth = window.speechSynthesis;
const Utterance = window.SpeechSynthesisUtterance;
const speaker = synth && Utterance ? new Speaker({ synth, Utterance }) : { say() {}, cancel() {} };
let audioCtx = null;
let speechUnlocked = false;

function getAudio() {
  if (!audioCtx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    audioCtx = new AC();
  }
  return audioCtx;
}

const ctx = {
  t: (key) => translate(lang, key),
  lang: () => lang,
  speaker,
  beep(level) {
    const ac = getAudio();
    if (ac) playBeep(ac, level);
  },
  // Call from a tap or click: browsers only allow sound after one.
  unlockAudio() {
    const ac = getAudio();
    if (ac && ac.state !== "running") ac.resume().catch(() => {});
    if (!speechUnlocked && synth && Utterance) {
      const u = new Utterance(" ");    // iPhone Safari speaks only after a first tap-started utterance
      u.volume = 0;
      synth.speak(u);
      speechUnlocked = true;
    }
  },
};

// Pages ----------------------------------------------------------------------
const pages = {
  netra: createNetra(ctx),
  rungu: createRungu(ctx),
  wicara: createWicara(ctx),
  latih: createLatih(ctx),
};
const TITLES = { netra: "netra_title", rungu: "rungu_title", wicara: "wicara_title", latih: "latih_title" };
const main = document.getElementById("main");
const home = document.getElementById("home");
for (const page of Object.values(pages)) main.append(page.el);

let current = null;    // "home" or a page name

function heading() {
  return (current === "home" ? home : pages[current].el).querySelector("h1");
}

function updateTitle() {
  document.title = current && current !== "home" ? `${ctx.t(TITLES[current])} · SenseBridge` : "SenseBridge";
}

function route() {
  const name = location.hash.slice(1);
  const next = Object.hasOwn(pages, name) ? name : "home";
  if (next === current) return;
  const firstLoad = current === null;
  if (current && current !== "home") pages[current].hide();
  speaker.cancel();
  home.hidden = next !== "home";
  for (const [n, page] of Object.entries(pages)) page.el.hidden = n !== next;
  current = next;
  if (next !== "home") pages[next].show();
  updateTitle();
  if (!firstLoad) {
    window.scrollTo(0, 0);
    heading()?.focus({ preventScroll: true });
  }
}

window.addEventListener("hashchange", route);
window.addEventListener("pagehide", () => {
  if (current && current !== "home") pages[current].hide();
});
document.querySelector(".skip").addEventListener("click", (e) => {
  e.preventDefault();      // a "#main" hash would be read as a route
  heading()?.focus();
});

// Language -------------------------------------------------------------------
const langGroup = document.getElementById("lang");
const langButtons = [...langGroup.querySelectorAll("[data-lang]")];

function setLang(next, save = true) {
  lang = next;
  root.lang = next;
  if (save) saveSetting(storage, "lang", next);
  for (const b of langButtons) {
    const on = b.dataset.lang === next;
    b.setAttribute("aria-checked", String(on));
    b.tabIndex = on ? 0 : -1;
  }
  applyText(document.querySelector(".top"), ctx.t);
  applyText(home, ctx.t);
  document.querySelector(".skip").textContent = ctx.t("skip");
  for (const page of Object.values(pages)) page.setLang(next);
  updateTitle();
}

langGroup.addEventListener("click", (e) => {
  const b = e.target.closest("[data-lang]");
  if (b && b.dataset.lang !== lang) setLang(b.dataset.lang);
});
langGroup.addEventListener("keydown", (e) => {
  const step = { ArrowLeft: -1, ArrowUp: -1, ArrowRight: 1, ArrowDown: 1 }[e.key];
  if (!step) return;
  e.preventDefault();
  const i = langButtons.findIndex((b) => b.dataset.lang === lang);
  const b = langButtons[(i + step + langButtons.length) % langButtons.length];
  setLang(b.dataset.lang);
  b.focus();
});

// Large text and dark mode (same keys and behavior as the project page) -----
const large = document.getElementById("t-large");
const dark = document.getElementById("t-dark");
const lightQuery = window.matchMedia("(prefers-color-scheme: light)");

function isDark() {
  const theme = root.dataset.theme;
  return theme ? theme === "dark" : !lightQuery.matches;
}
function syncSwitches() {
  dark.setAttribute("aria-checked", String(isDark()));
  large.setAttribute("aria-checked", String(root.dataset.size === "large"));
}
dark.addEventListener("click", () => {
  root.dataset.theme = isDark() ? "light" : "dark";
  saveSetting(storage, "theme", root.dataset.theme);
  syncSwitches();
});
large.addEventListener("click", () => {
  if (root.dataset.size === "large") {
    delete root.dataset.size;
    saveSetting(storage, "size", null);
  } else {
    root.dataset.size = "large";
    saveSetting(storage, "size", "large");
  }
  syncSwitches();
});
lightQuery.addEventListener("change", syncSwitches);

setLang(lang, false);
syncSwitches();
route();
