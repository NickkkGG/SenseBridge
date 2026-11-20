import { test } from "node:test";
import assert from "node:assert/strict";
import { Speaker, pickVoice, beepPattern } from "../../site/js/speaker.js";

class FakeUtterance { constructor(text) { this.text = text; } }
const fakeSynth = (voices = []) => ({
  spoken: [], cancelled: 0, getVoices: () => voices,
  speak(u) { this.spoken.push(u); }, cancel() { this.cancelled++; },
});
const make = (synth, now = () => 0) => new Speaker({ synth, Utterance: FakeUtterance, now });

test("speaks with the language code and a matching voice", () => {
  const damayanti = { lang: "id-ID", name: "Damayanti" };
  const synth = fakeSynth([{ lang: "en-US", name: "Samantha" }, damayanti]);
  make(synth).say("Halo", "id");
  assert.equal(synth.spoken[0].text, "Halo");
  assert.equal(synth.spoken[0].lang, "id-ID");
  assert.equal(synth.spoken[0].voice, damayanti);
});
test("waits for the current sentence, then speaks the next", () => {
  const synth = fakeSynth(); const s = make(synth);
  s.say("satu", "id"); s.say("dua", "id");
  assert.equal(synth.spoken.length, 1);
  synth.spoken[0].onend();
  assert.deepEqual(synth.spoken.map((u) => u.text), ["satu", "dua"]);
});
test("interrupt cancels what is playing and drops the queue", () => {
  const synth = fakeSynth(); const s = make(synth);
  s.say("satu", "id"); s.say("dua", "id"); s.say("Awas!", "id", { interrupt: true });
  assert.equal(synth.cancelled, 1);
  synth.spoken[0].onend();                     // the cancelled one ends late
  assert.deepEqual(synth.spoken.map((u) => u.text), ["satu", "Awas!"]);
  synth.spoken[1].onend();
  assert.equal(synth.spoken.length, 2);        // "dua" was dropped
});
test("sentences older than 6 s are skipped", () => {
  let now = 0; const synth = fakeSynth(); const s = make(synth, () => now);
  s.say("satu", "id"); now = 1; s.say("dua", "id"); now = 2; s.say("tiga", "id");
  now = 7.5; synth.spoken[0].onend();
  assert.deepEqual(synth.spoken.map((u) => u.text), ["satu", "tiga"]);
});
test("still speaks, with the language set, when no voice fits", () => {
  const synth = fakeSynth([{ lang: "fr-FR", name: "Amelie" }]);
  make(synth).say("Halo", "id");
  assert.equal(synth.spoken[0].lang, "id-ID");
  assert.equal(synth.spoken[0].voice, undefined);
});
test("pickVoice understands id-ID, id_ID and Android's in_ID", () => {
  assert.equal(pickVoice([{ lang: "in_ID", name: "x" }], "id").name, "x");
  assert.equal(pickVoice([{ lang: "id_ID", name: "y" }], "id").name, "y");
  assert.equal(pickVoice([{ lang: "en-GB", name: "g" }, { lang: "en-US", name: "u" }], "en").name, "u");
  assert.equal(pickVoice([{ lang: "fr-FR", name: "f" }], "id"), null);
});
test("beeps: level+1 tones, 1800 Hz for danger, 1000 Hz otherwise, 130 ms each", () => {
  assert.deepEqual(beepPattern(2), [
    { freq: 1800, start: 0, dur: 0.13 }, { freq: 1800, start: 0.2, dur: 0.13 }, { freq: 1800, start: 0.4, dur: 0.13 }]);
  assert.deepEqual(beepPattern(1).map((b) => b.freq), [1000, 1000]);
});
