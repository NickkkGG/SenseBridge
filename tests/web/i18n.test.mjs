import { test } from "node:test";
import assert from "node:assert/strict";
import { STRINGS, QUICK, SUGGEST, t } from "../../site/js/i18n.js";

test("both languages have the same keys", () => {
  assert.deepEqual(Object.keys(STRINGS.en).sort(), Object.keys(STRINGS.id).sort());
});
test("Farid's quick phrases and word suggestions are kept", () => {
  assert.deepEqual(QUICK.id, ["Halo", "Terima kasih", "Tolong", "Ya", "Tidak", "Maaf", "Saya butuh bantuan", "Di mana toilet?"]);
  assert.equal(QUICK.en.length, 8);
  assert.equal(SUGGEST.id[0], "_diam");
});
test("t() falls back to Indonesian, then to the key", () => {
  assert.equal(t("id", "start"), "Mulai");
  assert.equal(t("en", "start"), "Start");
  assert.equal(t("fr", "start"), "Mulai");
  assert.equal(t("id", "no_such_key"), "no_such_key");
});
test("no emoji or pictographs in interface text", () => {
  const all = [...Object.values(STRINGS.id), ...Object.values(STRINGS.en)].join(" ");
  assert.doesNotMatch(all, /\p{Extended_Pictographic}/u);
});
