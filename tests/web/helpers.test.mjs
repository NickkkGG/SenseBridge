import { test } from "node:test";
import assert from "node:assert/strict";
import { loadSettings, saveSetting } from "../../site/js/settings.js";
import { shouldMirror, mediaErrorKey, keepScreenOn } from "../../site/js/media.js";
import { undoWord } from "../../site/js/compose.js";

const blocked = { getItem() { throw new Error("blocked"); }, setItem() { throw new Error("blocked"); } };

test("settings fall back to defaults when storage is empty or blocked", () => {
  const defaults = { lang: "id", theme: null, size: null };
  assert.deepEqual(loadSettings({ getItem: () => null }), defaults);
  assert.deepEqual(loadSettings(blocked), defaults);
  assert.doesNotThrow(() => saveSetting(blocked, "lang", "en"));
});
test("settings read the project page's keys and reject unknown values", () => {
  const data = { "sb-lang": "en", "sb-theme": "light", "sb-size": "large" };
  assert.deepEqual(loadSettings({ getItem: (k) => data[k] ?? null }), { lang: "en", theme: "light", size: "large" });
  assert.equal(loadSettings({ getItem: (k) => (k === "sb-lang" ? "fr" : null) }).lang, "id");
});
test("only a camera that faces the user is mirrored", () => {
  const track = (facingMode) => ({ getSettings: () => ({ facingMode }) });
  assert.equal(shouldMirror(track("environment")), false);
  assert.equal(shouldMirror(track("user")), true);
  assert.equal(shouldMirror(track(undefined)), true);
});
test("camera and microphone errors map to messages", () => {
  const err = (name) => Object.assign(new Error(name), { name });
  assert.equal(mediaErrorKey(err("NotAllowedError"), "camera"), "perm_camera");
  assert.equal(mediaErrorKey(err("SecurityError"), "mic"), "perm_mic");
  assert.equal(mediaErrorKey(err("NotFoundError"), "camera"), "no_camera");
  assert.equal(mediaErrorKey(err("OverconstrainedError"), "camera"), "no_camera");
  assert.equal(mediaErrorKey(err("NotReadableError"), "mic"), "mic_busy");
  assert.equal(mediaErrorKey(err("AbortError"), "camera"), "cam_error");
});
test("undo removes the last word like the desktop app", () => {
  assert.equal(undoWord("halo apa kabar "), "halo apa ");
  assert.equal(undoWord("halo"), "");
  assert.equal(undoWord("   "), "");
});

function wakeEnv({ supported = true } = {}) {
  const env = { requests: 0, released: 0, listeners: {}, visibilityState: "visible" };
  env.doc = {
    get visibilityState() { return env.visibilityState; },
    addEventListener: (type, fn) => { env.listeners[type] = fn; },
    removeEventListener: (type) => { delete env.listeners[type]; },
  };
  env.nav = supported
    ? { wakeLock: { request: async () => { env.requests++; return { release: async () => { env.released++; } }; } } }
    : {};
  return env;
}
const flush = () => new Promise((r) => setTimeout(r, 0));

test("the screen stays on while a page runs and may sleep after", async () => {
  const env = wakeEnv(); const lock = keepScreenOn(env.nav, env.doc);
  await flush();
  assert.equal(env.requests, 1);
  lock.release(); await flush();
  assert.equal(env.released, 1);
});
test("the screen lock is asked for again when the page comes back into view", async () => {
  const env = wakeEnv(); const lock = keepScreenOn(env.nav, env.doc); await flush();
  env.visibilityState = "hidden"; env.listeners.visibilitychange();
  env.visibilityState = "visible"; env.listeners.visibilitychange(); await flush();
  assert.equal(env.requests, 2);
  lock.release();
});
test("a screen lock that arrives after release is let go at once", async () => {
  const env = wakeEnv(); const lock = keepScreenOn(env.nav, env.doc); lock.release(); await flush();
  assert.equal(env.released, 1);
});
test("browsers without a screen lock still work", () => {
  const env = wakeEnv({ supported: false });
  assert.doesNotThrow(() => keepScreenOn(env.nav, env.doc).release());
});
