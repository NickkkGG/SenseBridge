import { test } from "node:test";
import assert from "node:assert/strict";
import { assess, heightLevel, AlertGate, fromMediaPipe } from "../../site/js/obstacles.js";

const W = 640, H = 480;
const box = (name, x1, y1, x2, y2, score = 0.9) => ({ name, score, x1, y1, x2, y2 });

test("nothing close: level 0, ahead, no text", () => {
  assert.deepEqual(assess([], W, H, "id"), { level: 0, text: "", zone: "center", det: null });
  assert.equal(assess([box("person", 0, 0, 100, 0.39 * H)], W, H, "id").level, 0);
});
test("box height sets the level: 0.40 caution, 0.65 danger", () => {
  assert.equal(heightLevel(box("chair", 0, 0, 100, 0.40 * H), H), 1);
  assert.equal(assess([box("chair", 0, 0, 100, 0.65 * H)], W, H, "id").level, 2);
});
test("sensitivity scales the height", () => {
  assert.equal(assess([box("chair", 0, 0, 100, 0.30 * H)], W, H, "id", 1.6).level, 1);
  assert.equal(assess([box("chair", 0, 0, 100, 0.45 * H)], W, H, "id", 0.6).level, 0);
});
test("thirds give left, ahead, right", () => {
  const zone = (x1, x2) => assess([box("person", x1, 0, x2, 0.5 * H)], W, H, "en").zone;
  assert.equal(zone(0, 200), "left");
  assert.equal(zone(220, 420), "center");
  assert.equal(zone(440, 640), "right");
});
test("the tallest close box wins", () => {
  const r = assess([box("chair", 0, 0, 100, 0.5 * H), box("person", 500, 0, 640, 0.7 * H)], W, H, "id");
  assert.equal(r.det.name, "person");
  assert.equal(r.level, 2);
});
test("Farid's sentences in both languages", () => {
  assert.equal(assess([box("person", 500, 0, 640, 0.7 * H)], W, H, "id").text, "Awas! orang sangat dekat di kanan");
  assert.equal(assess([box("chair", 0, 0, 100, 0.5 * H)], W, H, "id").text, "Hati-hati, ada kursi di kiri");
  assert.equal(assess([box("person", 500, 0, 640, 0.7 * H)], W, H, "en").text, "Watch out! person very close on the right");
  assert.equal(assess([box("chair", 250, 0, 400, 0.5 * H)], W, H, "en").text, "Careful, chair ahead");
  assert.equal(assess([box("umbrella", 250, 0, 400, 0.5 * H)], W, H, "id").text, "Hati-hati, ada umbrella di depan");
});
test("alert gate: the first warning fires even right after page load", () => {
  assert.equal(new AlertGate().shouldAlert(1, "a", 0.5), true);
});
test("alert gate keeps the desktop timing", () => {
  const g = new AlertGate();
  assert.equal(g.shouldAlert(0, "", 10), false);
  assert.equal(g.shouldAlert(1, "a", 10), true);
  assert.equal(g.shouldAlert(1, "b", 11.1), false);  // under 1.2 s since the last one
  assert.equal(g.shouldAlert(1, "b", 11.3), true);   // new sentence
  assert.equal(g.shouldAlert(1, "b", 15.2), false);  // same caution sentence before 4 s
  assert.equal(g.shouldAlert(1, "b", 15.4), true);
  assert.equal(g.shouldAlert(2, "c", 16.7), true);
  assert.equal(g.shouldAlert(2, "c", 18.6), false);  // same danger sentence before 2 s
  assert.equal(g.shouldAlert(2, "c", 18.8), true);
});
test("MediaPipe detections become pixel boxes, mirrored for a front camera", () => {
  const result = { detections: [{ categories: [{ categoryName: "person", score: 0.8 }], boundingBox: { originX: 10, originY: 20, width: 100, height: 200 } }] };
  assert.deepEqual(fromMediaPipe(result, 640, false), [{ name: "person", score: 0.8, x1: 10, y1: 20, x2: 110, y2: 220 }]);
  assert.deepEqual(fromMediaPipe(result, 640, true), [{ name: "person", score: 0.8, x1: 530, y1: 20, x2: 630, y2: 220 }]);
  assert.deepEqual(fromMediaPipe({ detections: [] }, 640, false), []);
});
