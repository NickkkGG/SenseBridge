// Small DOM helpers shared by the shell and the pages.

// h("p", {class: "note", "data-t": "disclaimer"}, child, ...) -> element.
// Props starting with "on" become event listeners; true/false/null props are
// boolean attributes.
export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === null || value === undefined || value === false) continue;
    if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2), value);
    else if (key === "class") el.className = value;
    else if (key === "style") el.style.cssText = value;
    else el.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat()) {
    if (child !== null && child !== undefined && child !== false) el.append(child);
  }
  return el;
}

// Inline SVG icon from markup (parsed by the HTML parser, so namespaces are right).
export function svg(markup) {
  const tpl = document.createElement("template");
  tpl.innerHTML = markup.trim();
  return tpl.content.firstElementChild;
}

export const ICON_BACK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';

// Fills every [data-t] (text), [data-t-placeholder] and [data-t-label]
// (aria-label) under root with the current language.
export function applyText(root, t) {
  for (const el of root.querySelectorAll("[data-t]")) el.textContent = t(el.dataset.t);
  for (const el of root.querySelectorAll("[data-t-placeholder]")) el.placeholder = t(el.dataset.tPlaceholder);
  for (const el of root.querySelectorAll("[data-t-label]")) el.setAttribute("aria-label", t(el.dataset.tLabel));
}

// The frame every line page shares: back link, numbered title, gloss and the
// colored bar. Returns the section and the empty body to fill.
export function basePage({ line, num, titleKey, subKey }) {
  const body = h("div", { class: "wrap page-body" });
  const el = h("section", { class: "page", style: `--c: var(--${line})`, hidden: true, "aria-labelledby": `${line}-title` },
    h("div", { class: "wrap page-head" },
      h("a", { class: "back", href: "#" }, svg(ICON_BACK), h("span", { "data-t": "all_lines" })),
      h("div", { class: "title-row" },
        h("span", { class: "badge", "aria-hidden": "true" }, String(num)),
        h("h1", { id: `${line}-title`, tabindex: "-1", "data-t": titleKey })),
      h("p", { class: "gloss", "data-t": subKey })),
    h("div", { class: "page-bar" }),
    body);
  return { el, body };
}

// A switch button like the project page's: <button role=switch>label<track>.
export function switchButton(labelKey, checked, onChange) {
  const btn = h("button", { class: "switch", type: "button", role: "switch", "aria-checked": String(checked) },
    h("span", { "data-t": labelKey }), h("span", { class: "track", "aria-hidden": "true" }));
  btn.addEventListener("click", () => {
    const next = btn.getAttribute("aria-checked") !== "true";
    btn.setAttribute("aria-checked", String(next));
    onChange(next);
  });
  return btn;
}
