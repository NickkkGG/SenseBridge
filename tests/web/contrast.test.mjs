import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../../site/css/app.css", import.meta.url), "utf8");

// Custom properties declared in the first rule that starts with `selector`.
function tokens(selector) {
  const start = css.indexOf(selector);
  assert.notEqual(start, -1, `missing ${selector}`);
  const body = css.slice(css.indexOf("{", start) + 1, css.indexOf("}", start));
  return Object.fromEntries([...body.matchAll(/(--[\w-]+):\s*([^;]+);/g)].map((m) => [m[1], m[2].trim()]));
}
function luminance(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrast(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

test("error text is readable (4.5:1) on the page background in every theme", () => {
  const token = css.match(/\.status\.bad\s*\{\s*color:\s*var\((--[\w-]+)\)/)[1];
  const dark = tokens(":root {");
  const themes = {
    dark,
    "light (system)": { ...dark, ...tokens(':root:not([data-theme="dark"]) {') },
    "light (switch)": { ...dark, ...tokens(':root[data-theme="light"] {') },
  };
  for (const [name, t] of Object.entries(themes)) {
    const ratio = contrast(t[token], t["--bg"]);
    assert.ok(ratio >= 4.5, `${name}: ${t[token]} on ${t["--bg"]} is ${ratio.toFixed(2)}:1`);
  }
});
