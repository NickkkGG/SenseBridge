// Line 3: page frame only for now; its body comes with its own task.
import { basePage, applyText } from "../ui.js";

export function createPage(ctx) {
  const { el } = basePage({ line: "wicara", num: 3, titleKey: "wicara_title", subKey: "wicara_sub" });
  applyText(el, ctx.t);
  return { el, show() {}, hide() {}, setLang() { applyText(el, ctx.t); } };
}
