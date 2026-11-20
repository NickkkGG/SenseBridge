// Obstacle rules, ported from Farid's services.assess and BlindPage.alert.
// Browser-free: boxes in, level / sentence / zone out.
import { NAMES_ID, DIR } from "./i18n.js";

const CAUTION = 0.40;   // box height as a share of the frame height
const DANGER = 0.65;

// Det = {name, score, x1, y1, x2, y2}, pixels in display coordinates.
function heightRatio(det, H, sens) {
  return (det.y2 - det.y1) / H * sens;
}

export function heightLevel(det, H, sens = 1) {
  const hr = heightRatio(det, H, sens);
  return hr >= DANGER ? 2 : hr >= CAUTION ? 1 : 0;
}

// The tallest box that is close enough decides the warning.
export function assess(dets, W, H, lang, sens = 1) {
  let best = null, bestHr = 0;
  for (const det of dets) {
    const hr = heightRatio(det, H, sens);
    if (hr >= CAUTION && (best === null || hr > bestHr)) {
      best = det;
      bestHr = hr;
    }
  }
  if (best === null) return { level: 0, text: "", zone: "center", det: null };

  const level = bestHr >= DANGER ? 2 : 1;
  const cx = (best.x1 + best.x2) / 2;
  const zone = cx < W / 3 ? "left" : cx > 2 * W / 3 ? "right" : "center";
  let text;
  if (lang === "id") {
    const name = Object.hasOwn(NAMES_ID, best.name) ? NAMES_ID[best.name] : best.name;
    const where = DIR.id[zone];
    text = level === 2 ? `Awas! ${name} sangat dekat di ${where}` : `Hati-hati, ada ${name} di ${where}`;
  } else {
    const where = DIR.en[zone];
    text = level === 2 ? `Watch out! ${best.name} very close ${where}` : `Careful, ${best.name} ${where}`;
  }
  return { level, text, zone, det: best };
}

// When to speak or beep: at least 1.2 s between warnings; the same sentence
// repeats after 4 s (caution) or 2 s (danger). Times are in seconds.
export class AlertGate {
  constructor() {
    this.lastText = "";
    this.lastTime = -Infinity;
  }

  shouldAlert(level, text, now) {
    if (level === 0) return false;
    const cool = level === 2 ? 2.0 : 4.0;
    const since = now - this.lastTime;
    if ((text !== this.lastText || since > cool) && since > 1.2) {
      this.lastText = text;
      this.lastTime = now;
      return true;
    }
    return false;
  }
}

// MediaPipe ObjectDetector result -> Det[]. A mirrored (front camera) preview
// flips x so that "left" stays the user's left.
export function fromMediaPipe(result, W, mirror) {
  const dets = [];
  for (const d of result?.detections ?? []) {
    const c = d.categories?.[0];
    const b = d.boundingBox;
    if (!c || !b) continue;
    const x1 = mirror ? W - (b.originX + b.width) : b.originX;
    dets.push({ name: c.categoryName, score: c.score, x1, y1: b.originY, x2: x1 + b.width, y2: b.originY + b.height });
  }
  return dets;
}
