// Microphone level math and the loud-sound alert, ported from Farid's
// SpeechListener (services.py). Browser-free: samples in, numbers out.

// Root mean square of Web Audio samples (-1..1).
export function rms(samples) {
  if (!samples.length) return 0;
  let sum = 0;
  for (const s of samples) sum += s * s;
  return Math.sqrt(sum / samples.length);
}

// Decibels relative to full scale. The floor of 1/32768 matches the Python
// version's max(rms, 1) on 16-bit samples.
export function dbfs(rmsValue) {
  return 20 * Math.log10(Math.max(rmsValue, 1 / 32768));
}

// 0..1 for the level bar.
export function levelFromDbfs(d) {
  return Math.min(1, Math.max(0, (d + 60) / 60));
}

// Fires when the sound is louder than `threshold` dBFS and at least
// `cooldown` seconds have passed since the last alert.
export class LoudAlert {
  constructor({ threshold = -12, cooldown = 3 } = {}) {
    this.threshold = threshold;
    this.cooldown = cooldown;
    this.lastTime = -Infinity;
  }

  check(dbfsValue, now) {
    if (dbfsValue > this.threshold && now - this.lastTime >= this.cooldown) {
      this.lastTime = now;
      return true;
    }
    return false;
  }
}

// Analyser window and sampling interval for the level meter: a window of
// about 100 ms (Farid's listener blocks) read once per window, so every
// sample is checked and short bangs are not missed.
export function meterTiming(sampleRate) {
  const fftSize = Math.min(32768, Math.max(32, 2 ** Math.floor(Math.log2(sampleRate * 0.1))));
  return { fftSize, intervalMs: Math.floor((fftSize / sampleRate) * 1000) };
}
