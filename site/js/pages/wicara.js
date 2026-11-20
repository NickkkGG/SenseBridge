// Line 3, Tuna Wicara: typed words and quick phrases are spoken aloud
// (port of Farid's MutePage; lip reading comes in stage 2).
import { basePage, applyText, h } from "../ui.js";
import { undoWord } from "../compose.js";
import { QUICK } from "../i18n.js";

export function createPage(ctx) {
  const { el, body } = basePage({ line: "wicara", num: 3, titleKey: "wicara_title", subKey: "wicara_sub" });
  body.classList.add("wicara-grid");

  const box = h("textarea", { class: "msg-box", id: "wicara-msg", "data-t-placeholder": "msg_placeholder" });
  const speak = (text) => {
    ctx.unlockAudio();
    if (text.trim()) ctx.speaker.say(text.trim(), ctx.lang(), { interrupt: true });
  };
  const button = (cls, key, onClick) => h("button", { class: cls, type: "button", "data-t": key, onclick: onClick });
  const stops = h("ol", { class: "stops" });

  body.append(
    h("div", {},
      h("label", { class: "label", for: "wicara-msg", "data-t": "compose" }),
      box,
      h("div", { class: "actions" },
        button("go", "speak", () => speak(box.value)),
        button("plain", "undo_word", () => { box.value = undoWord(box.value); }),
        button("plain", "clear", () => { box.value = ""; })),
      h("p", { class: "note", "data-t": "lips_soon" })),
    h("div", {},
      h("h2", { class: "label", "data-t": "quick" }),
      stops),
  );

  // Farid's quick phrases: added to the message and spoken at once.
  function renderStops() {
    const phrases = QUICK[ctx.lang()] || QUICK.id;
    stops.replaceChildren(...phrases.map((phrase) => h("li", {},
      h("button", {
        type: "button",
        onclick: () => {
          box.value += phrase + " ";
          speak(phrase);
        },
      }, phrase))));
  }

  function setLang() {
    applyText(el, ctx.t);
    renderStops();
  }

  setLang();
  return { el, show() {}, hide() {}, setLang };
}
