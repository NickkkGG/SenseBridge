// Message editing for Tuna Wicara, ported from Farid's MutePage.undo.

// Removes the last word; keeps a trailing space when words remain.
export function undoWord(text) {
  const words = text.trim().split(/\s+/).filter(Boolean);
  return words.slice(0, -1).join(" ") + (words.length > 1 ? " " : "");
}
