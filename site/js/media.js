// Camera and microphone. shouldMirror and mediaErrorKey are browser-free;
// the open functions use navigator only when they are called.

// Mirror the preview only for a camera that faces the user, so "left" on
// screen is the user's left. A back camera is never mirrored.
export function shouldMirror(track) {
  return track?.getSettings?.().facingMode !== "environment";
}

// getUserMedia error -> interface string key.
export function mediaErrorKey(err, kind) {
  const camera = kind === "camera";
  switch (err?.name) {
    case "NotAllowedError":
    case "SecurityError":
      return camera ? "perm_camera" : "perm_mic";
    case "NotFoundError":
    case "OverconstrainedError":
      return camera ? "no_camera" : "no_mic";
    case "NotReadableError":
      return camera ? "cam_busy" : "mic_busy";
    default:
      return camera ? "cam_error" : "mic_error";
  }
}

export function stopStream(stream) {
  if (stream) for (const track of stream.getTracks()) track.stop();
}

// Opens the camera (the back one when there is one) and plays it in `video`.
export async function openCamera(video, facing = "environment") {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: { ideal: facing }, width: { ideal: 640 }, height: { ideal: 480 } },
    audio: false,
  });
  video.muted = true;
  video.playsInline = true;      // iPhone: play in the page, not full screen
  video.srcObject = stream;
  try {
    await video.play();
  } catch (err) {
    stopStream(stream);
    video.srcObject = null;
    throw err;
  }
  return stream;
}

// Raw microphone sound for the level bar and the loud-sound alert: no
// automatic gain or noise suppression, which would hide how loud it is.
export function openMic() {
  return navigator.mediaDevices.getUserMedia({
    audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
    video: false,
  });
}
