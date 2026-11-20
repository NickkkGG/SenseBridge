// Language, theme and text size, saved in the same localStorage keys as the
// project page (/about/). Storage can be missing or blocked (private window,
// blocked site data): then the defaults apply and nothing is saved.

const KEYS = { lang: "sb-lang", theme: "sb-theme", size: "sb-size" };
const VALID = { lang: ["id", "en"], theme: ["dark", "light"], size: ["large"] };

function read(storage, name) {
  try {
    const value = storage.getItem(KEYS[name]);
    return VALID[name].includes(value) ? value : null;
  } catch {
    return null;
  }
}

export function loadSettings(storage) {
  return { lang: read(storage, "lang") ?? "id", theme: read(storage, "theme"), size: read(storage, "size") };
}

export function saveSetting(storage, name, value) {
  try {
    if (value === null) storage.removeItem(KEYS[name]);
    else storage.setItem(KEYS[name], value);
  } catch {
    // Blocked storage: the setting lasts until the page closes.
  }
}
