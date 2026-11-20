// Line 4: page frame only for now; its body comes with its own task.
import { basePage, applyText } from "../ui.js";

export function createPage(ctx) {
  const { el } = basePage({ line: "latih", num: 4, titleKey: "latih_title", subKey: "latih_sub" });
  applyText(el, ctx.t);
  return { el, show() {}, hide() {}, setLang() { applyText(el, ctx.t); } };
}
