// Line 2: page frame only for now; its body comes with its own task.
import { basePage, applyText } from "../ui.js";

export function createPage(ctx) {
  const { el } = basePage({ line: "rungu", num: 2, titleKey: "rungu_title", subKey: "rungu_sub" });
  applyText(el, ctx.t);
  return { el, show() {}, hide() {}, setLang() { applyText(el, ctx.t); } };
}
