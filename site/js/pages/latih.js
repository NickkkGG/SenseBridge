// Line 4, Latih Model: placeholder until lip recording and training come to
// the browser in stage 2.
import { basePage, applyText, h } from "../ui.js";

export function createPage(ctx) {
  const { el, body } = basePage({ line: "latih", num: 4, titleKey: "latih_title", subKey: "latih_sub" });
  body.append(h("p", { class: "note", "data-t": "latih_soon" }));
  const setLang = () => applyText(el, ctx.t);
  setLang();
  return { el, show() {}, hide() {}, setLang };
}
