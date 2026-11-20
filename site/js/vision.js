// MediaPipe object detector (EfficientDet-Lite0, COCO classes), loaded from
// jsDelivr and Google's model bucket the first time Tuna Netra starts.

const BUNDLE = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/vision_bundle.mjs";
const WASM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm";
const MODEL = "https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/float16/1/efficientdet_lite0.tflite";

let pending = null;

// One detector for the whole visit. A failed load is forgotten, so pressing
// Start again retries (for example after the internet comes back).
export function createObjectDetector() {
  if (!pending) {
    pending = load().catch((err) => {
      pending = null;
      throw err;
    });
  }
  return pending;
}

async function load() {
  const { FilesetResolver, ObjectDetector } = await import(BUNDLE);
  const fileset = await FilesetResolver.forVisionTasks(WASM);
  const options = (delegate) => ({
    baseOptions: { modelAssetPath: MODEL, delegate },
    runningMode: "VIDEO",
    scoreThreshold: 0.4,      // Farid's YOLO conf
    maxResults: 8,
  });
  try {
    return await ObjectDetector.createFromOptions(fileset, options("GPU"));
  } catch {
    return await ObjectDetector.createFromOptions(fileset, options("CPU"));
  }
}
