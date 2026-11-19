# SenseBridge

SenseBridge is a desktop assistant for students with disabilities. It uses a laptop's camera and microphone to turn one sense into another: what is in front of the camera becomes a spoken warning, speech becomes large captions, and lip movements or typing become a voice. The interface is in Indonesian and English.

Originally built by Farid as **AksesKita**. Mac support, the working microphone page, lip-model training and tests were added by Nick.

Project page: https://sensebridge-omega.vercel.app (source in [`site/`](site/))

## What it does

| Page | Takes | Gives |
|---|---|---|
| Tuna Netra (visually impaired) | Camera | Obstacles found by YOLOv8n, spoken with their side (left, ahead, right) and a beep |
| Tuna Rungu (deaf) | Microphone, camera | Speech as large live captions with history, a loud-sound alert, lip reading |
| Tuna Wicara (speech impaired) | Lips, typing, quick phrases | A computer voice through the speaker |
| Latih Model (train) | Short recordings of each word | A personal lip-reading model |

Lip reading only knows the words you record yourself: about 30 one-second clips per word, plus the closed-mouth class `_diam`, recorded on the Latih Model page.

## Run it

Needs Python 3.11 or 3.12 (mediapipe 0.10.14 does not support 3.13) and a webcam.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

On Windows use `.venv\Scripts\python` instead of `.venv/bin/python`. `run.py` starts the same window after checking Python, the files and the libraries. Mac notes (VSCode, camera and microphone permissions, troubleshooting) are in [HOW-TO-RUN-MAC.md](HOW-TO-RUN-MAC.md), in Indonesian.

Tests: `.venv/bin/python -m unittest discover tests`

## Files

- `main.py`: the window and its four pages
- `services.py`: voice output, microphone listener, obstacle detector, lip engine
- `lipcore.py`: mouth crop and the lip model (3D CNN + GRU)
- `train.py`: trains the lip model from `dataset/<lang>/<word>/*.npy`
- `record.py`: records clips from the terminal
- `strings.py`: interface text in both languages

## Privacy and limits

Recordings (`dataset/`) and trained models (`models/`) contain the user's face. They stay on the computer and are ignored by git. Captions send the recorded speech to Google Speech, so they need an internet connection.

SenseBridge is an extra aid, not a replacement for a cane or a guide. Distance is an estimate, and stairs, holes and glass are not detected.
