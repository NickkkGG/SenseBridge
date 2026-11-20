# SenseBridge

SenseBridge is an assistant for students with disabilities. It uses a camera and a microphone to turn one sense into another: what is in front of the camera becomes a spoken warning, speech becomes large captions, and typing (and, in the desktop app, lip movements) becomes a voice. The interface is in Indonesian and English.

Originally built by Farid as **AksesKita**. The web version, Mac support, the working microphone page, lip-model training and tests were added by Nick.

## Use it in a browser

Open https://sensebridge-omega.vercel.app on a phone or a laptop, pick a line and allow the camera or the microphone. Nothing to install.

| Line | Takes | Gives |
|---|---|---|
| 1 Tuna Netra (visually impaired) | Camera (the back camera on a phone) | Close obstacles as a spoken warning with their side (left, ahead, right), a beep and a large status board |
| 2 Tuna Rungu (deaf) | Microphone | Speech as large live captions with a timed history, and a banner for loud sounds |
| 3 Tuna Wicara (speech impaired) | Typing, quick phrases | A voice through the speaker |
| 4 Latih Model (train) | Not in the browser yet | Lip reading and lip-model training come to the browser next; use the desktop app for now |

- Browsers: Chrome, Edge or Safari. Firefox has no speech recognition, so it shows no captions; its loud-sound alert still works.
- Camera images and microphone sound are used on the device and never stored. Obstacles are found in the browser by MediaPipe's EfficientDet-Lite0 model (about 18 MB with its runtime, downloaded once). Captions come from the browser's own speech recognition, which sends the speech to Google (Chrome), Microsoft (Edge) or Apple (Safari), so they need the internet.
- The project page is at https://sensebridge-omega.vercel.app/about/.
- Source: [`site/`](site/), plain HTML, CSS and JavaScript modules with no build step. To publish a new version, deploy a copy of `site/` from outside this repository. Vercel blocks deploys made inside it because the commit author is not a member of the Vercel team. From the project folder:

  ```bash
  rm -rf /tmp/sensebridge-site && cp -R site /tmp/sensebridge-site && (cd /tmp/sensebridge-site && npx --yes vercel@latest deploy --prod --yes); rm -rf /tmp/sensebridge-site
  ```

## Desktop app (Python)

The full app, with lip reading and lip-model training, runs on a laptop with a webcam.

| Page | Takes | Gives |
|---|---|---|
| Tuna Netra (visually impaired) | Camera | Obstacles found by YOLOv8n, spoken with their side (left, ahead, right) and a beep |
| Tuna Rungu (deaf) | Microphone, camera | Speech as large live captions with history, a loud-sound alert, lip reading |
| Tuna Wicara (speech impaired) | Lips, typing, quick phrases | A computer voice through the speaker |
| Latih Model (train) | Short recordings of each word | A personal lip-reading model |

Lip reading only knows the words you record yourself: about 30 one-second clips per word, plus the closed-mouth class `_diam`, recorded on the Latih Model page.

### Run it

Needs Python 3.11 or 3.12 (mediapipe 0.10.14 does not support 3.13) and a webcam.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

On Windows use `.venv\Scripts\python` instead of `.venv/bin/python`. `run.py` starts the same window after checking Python, the files and the libraries. Mac notes (VSCode, camera and microphone permissions, troubleshooting) are in [HOW-TO-RUN-MAC.md](HOW-TO-RUN-MAC.md), in Indonesian.

Tests: `.venv/bin/python -m unittest discover tests` for the desktop app and `node --test "tests/web/*.test.mjs"` (Node 22 or newer) for the web app's logic.

## Files

- `main.py`: the window and its four pages
- `services.py`: voice output, microphone listener, obstacle detector, lip engine
- `lipcore.py`: mouth crop and the lip model (3D CNN + GRU)
- `train.py`: trains the lip model from `dataset/<lang>/<word>/*.npy`
- `record.py`: records clips from the terminal
- `strings.py`: interface text in both languages
- `site/`: the web app (`index.html`, `js/main.js` for the header and routing, `js/pages/` one file per line, browser-free logic such as `js/obstacles.js` and `js/captions.js` tested in `tests/web/`) and the project page in `site/about/`

## Privacy and limits

Recordings (`dataset/`) and trained models (`models/`) contain the user's face. They stay on the computer and are ignored by git. The desktop app's captions send the recorded speech to Google Speech, and the web app's captions go through the browser's own speech service, so both need an internet connection.

SenseBridge is an extra aid, not a replacement for a cane or a guide. Distance is an estimate, and stairs, holes and glass are not detected.
