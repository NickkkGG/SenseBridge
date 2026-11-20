// Line 1: page frame only for now; its body comes with its own task.
import { basePage, applyText } from "../ui.js";

export function createPage(ctx) {
  const { el } = basePage({ line: "netra", num: 1, titleKey: "netra_title", subKey: "netra_sub" });
  applyText(el, ctx.t);
  return { el, show() {}, hide() {}, setLang() { applyText(el, ctx.t); } };
}
