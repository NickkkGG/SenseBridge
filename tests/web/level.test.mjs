import { test } from "node:test";
import assert from "node:assert/strict";
import { rms, dbfs, levelFromDbfs, LoudAlert } from "../../site/js/level.js";

test("rms and dBFS match the Python listener", () => {
  assert.equal(rms(new Float32Array([0.5, -0.5])), 0.5);
  assert.equal(dbfs(1), 0);
  assert.ok(Math.abs(dbfs(0) - 20 * Math.log10(1 / 32768)) < 1e-9);
  assert.ok(Math.abs(dbfs(0.5) + 6.0206) < 1e-3);
});
test("level bar is (dBFS + 60) / 60, clamped", () => {
  assert.equal(levelFromDbfs(-60), 0);
  assert.equal(levelFromDbfs(-30), 0.5);
  assert.equal(levelFromDbfs(0), 1);
  assert.equal(levelFromDbfs(-90), 0);
  assert.equal(levelFromDbfs(3), 1);
});
test("loud alert above -12 dBFS with a 3 s cooldown", () => {
  const a = new LoudAlert();
  assert.equal(a.check(-12, 0), false);
  assert.equal(a.check(-11, 0.5), true);
  assert.equal(a.check(-5, 3.49), false);
  assert.equal(a.check(-5, 3.5), true);
});
