import { test } from "node:test";
import assert from "node:assert/strict";
import { CaptionController, getRecognitionCtor } from "../../site/js/captions.js";

class FakeRec {
  constructor() { FakeRec.last = this; this.starts = 0; this.stops = 0; }
  start() { this.starts++; } stop() { this.stops++; } abort() { this.stops++; }
}
const result = (text, isFinal) => Object.assign([{ transcript: text }], { isFinal });
const event = (...results) => ({ resultIndex: 0, results });
function make(extra = {}) {
  const got = { interim: [], final: [], errors: [], status: [] };
  const c = new CaptionController({
    Recognition: FakeRec, lang: "id", schedule: (fn) => fn(),
    onInterim: (x) => got.interim.push(x), onFinal: (x) => got.final.push(x),
    onError: (x) => got.errors.push(x), onStatus: (x) => got.status.push(x), ...extra,
  });
  return { c, got };
}

test("starts continuous recognition with interim results in Indonesian", () => {
  const { c } = make(); c.start(); const r = FakeRec.last;
  assert.equal(r.continuous, true); assert.equal(r.interimResults, true);
  assert.equal(r.lang, "id-ID"); assert.equal(r.starts, 1);
});
test("final text is trimmed and capitalised, interim text passes through", () => {
  const { c, got } = make(); c.start(); const r = FakeRec.last;
  r.onresult(event(result("halo apa", false)));
  r.onresult(event(result(" halo apa kabar ", true)));
  r.onresult(event(result("  ", true)));
  assert.deepEqual(got.interim, ["halo apa"]);
  assert.deepEqual(got.final, ["Halo apa kabar"]);
});
test("restarts when the browser ends the session, but not after stop()", () => {
  const { c } = make(); c.start(); const r = FakeRec.last;
  r.onend(); assert.equal(r.starts, 2);
  c.stop(); r.onend(); assert.equal(r.starts, 2);
});
test("permission denied is reported and not retried", () => {
  const { c, got } = make(); c.start(); const r = FakeRec.last;
  r.onerror({ error: "not-allowed" }); r.onend();
  assert.deepEqual(got.errors, ["perm_mic"]); assert.equal(r.starts, 1);
});
test("a network error is reported and retried after one second", () => {
  const waits = [];
  const { c, got } = make({ schedule: (fn, ms) => { waits.push(ms); fn(); } });
  c.start(); const r = FakeRec.last;
  r.onerror({ error: "network" }); r.onend();
  assert.deepEqual(got.errors, ["err_net"]); assert.deepEqual(waits, [1000]); assert.equal(r.starts, 2);
});
test("silence is not an error", () => {
  const { c, got } = make(); c.start(); const r = FakeRec.last;
  r.onerror({ error: "no-speech" }); r.onend();
  assert.deepEqual(got.errors, []); assert.equal(r.starts, 2);
});
test("changing language while listening restarts in English", () => {
  const { c } = make(); c.start(); const old = FakeRec.last;
  c.setLang("en"); old.onend();
  assert.notEqual(FakeRec.last, old); assert.equal(FakeRec.last.lang, "en-US");
  assert.equal(FakeRec.last.starts, 1); assert.equal(old.starts, 1);
});
test("finds the prefixed constructor and reports none in Firefox", () => {
  assert.equal(getRecognitionCtor({ webkitSpeechRecognition: FakeRec }), FakeRec);
  assert.equal(getRecognitionCtor({}), null);
});
test("restarts with the browser's setTimeout, which must not be called as a method", () => {
  function strictSchedule(fn) {
    if (this !== undefined && this !== globalThis) throw new TypeError("Illegal invocation");
    fn();
  }
  const { c } = make({ schedule: strictSchedule }); c.start(); const r = FakeRec.last;
  r.onend();
  assert.equal(r.starts, 2);
});
