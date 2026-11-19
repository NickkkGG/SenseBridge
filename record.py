"""record_all.py - rekam beberapa kata berurutan
Pakai:  python record_all.py id 30
"""
import os
import sys
import time

import cv2
import numpy as np

import lipcore as lc

lang, n = sys.argv[1], int(sys.argv[2])
WORDS = ["_diam", "tolong", "ya", "tidak"]       # ubah sesuai kebutuhan

cap = cv2.VideoCapture(0)
fm = lc.mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True,
                         min_detection_confidence=0.5,
                         min_tracking_confidence=0.5)


def grab(msg):
    ok, frame = cap.read()
    if not ok:
        return None
    frame = cv2.flip(frame, 1)
    res = fm.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    roi = None
    if res.multi_face_landmarks:
        roi, (x1, y1, x2, y2) = lc.get_mouth_roi(
            frame, res.multi_face_landmarks[0].landmark)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (88, 199, 52), 2)
    cv2.putText(frame, msg, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                (60, 60, 255), 3)
    cv2.imshow("record", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        sys.exit()
    return roi


for word in WORDS:
    out = os.path.join(lc.DATA_DIR, lang, word)
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    while time.time() - t0 < 5:                  # jeda antar kata
        grab(f"Berikutnya: {word}  ({5 - int(time.time() - t0)})")
    for i in range(n):
        t0 = time.time()
        while time.time() - t0 < 2:              # hitung mundur
            grab(f"{word} {i + 1}/{n}  siap")
        frames = []
        while len(frames) < lc.SEQ_LEN:
            roi = grab(f"REC {word}")
            if roi is not None:
                frames.append(roi)
        np.save(os.path.join(out, f"{int(time.time() * 1000)}.npy"),
                np.stack(frames))
        print(f"{word}: {i + 1}/{n}")

cap.release()
cv2.destroyAllWindows()
print(train_msg := "Rekam selesai. Sekarang latih model.")