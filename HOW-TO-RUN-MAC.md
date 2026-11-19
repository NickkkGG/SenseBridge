# Cara menjalankan SenseBridge di Mac

Sudah disiapkan dan dites di MacBook Pro M1 Pro (macOS 27.2) dengan Python 3.12 (folder `.venv`) dan VSCode 1.146.

## Jalankan dari VSCode

1. Buka VSCode, pilih **File → Open Folder…**, lalu pilih folder project ini.
   Kalau muncul *"Do you trust the authors of the files in this folder?"*, pilih **Yes, I trust the authors**.
2. Buka `main.py`. Di pojok kanan bawah harus tertulis **3.12 (.venv)**.
   Kalau beda: tekan `Cmd+Shift+P` → **Python: Select Interpreter** → pilih `./.venv/bin/python`.
3. Tekan **Ctrl+F5** (Run Without Debugging). Konfigurasi **Jalankan SenseBridge** sudah disiapkan.
   Pakai **F5** kalau mau debugging dengan breakpoint.
4. Saat pertama kali jalan, macOS akan bertanya *"Visual Studio Code" would like to access the camera*. Klik **Allow**.
   Kamera akan muncul sendiri dalam ±3 detik, tidak perlu restart.
5. Saat pertama kali menekan **Aktifkan mikrofon** di halaman Tuna Rungu, macOS akan menanyakan izin mikrofon. Klik **Allow**.
6. Untuk berhenti, tutup jendela SenseBridge.

Peluncuran pertama bisa 10–30 detik karena torch dan mediapipe dimuat dulu. Berikutnya lebih cepat.

## Jalankan dari Terminal

Buka terminal di folder project (di VSCode: menu **Terminal → New Terminal**), lalu:

```bash
source .venv/bin/activate
python main.py
```

`python run.py` juga bisa: itu launcher yang mengecek Python, file, dan library dulu sebelum membuka `main.py`.
Kalau dijalankan dari aplikasi Terminal, izin kamera dan mikrofon yang diminta untuk Terminal, bukan VSCode.

## Status fitur

| Halaman | Yang bisa dipakai | Catatan |
|---|---|---|
| Tuna Netra | Deteksi hambatan (YOLO), zona kiri/depan/kanan, peringatan suara, bunyi bip | – |
| Tuna Wicara | Ketik pesan atau kalimat cepat lalu diucapkan, deteksi wajah, mulut buka/tutup, baca bibir | Baca bibir butuh model dulu (lihat di bawah) |
| Tuna Rungu | Ucapan jadi teks besar dan riwayat (butuh internet), bar volume, peringatan suara keras, baca bibir | Pengenalan suara butuh internet; baca bibir butuh model |
| Latih Model | Rekam klip kata, latih model | – |

## Bikin model baca bibir

Model belum ada sampai kamu merekam dan melatihnya sendiri. Model disimpan per bahasa (`models/lip_id.pt` atau `models/lip_en.pt`), dan paling akurat untuk orang yang merekam klipnya.

1. Buka halaman **Latih Model** (bahasa yang dipilih di sidebar = bahasa modelnya).
2. Mulai dengan kata `_diam` ditambah 3–5 kata, misalnya `tolong`, `ya`, `tidak`.
3. Pilih kata, klik **Rekam klip**. Setelah hitung mundur 3, ucapkan katanya selama ±1 detik. Untuk `_diam`, tutup mulut saja.
4. Ulangi sampai ±30 klip per kata. Variasikan sedikit posisi kepala dan cahaya supaya model tidak hanya hafal satu kondisi.
5. Pilih **Epoch** 50, lalu klik **Latih model**. Log menampilkan akurasi uji tiap 5 epoch. Perkiraan waktunya 5–7 menit untuk 8 kata × 30 klip, dan aplikasi tetap bisa dipakai selama itu.
6. Setelah muncul **✔ Model siap dipakai**, buka Tuna Wicara: gerakan bibir akan jadi kata di kotak pesan.

Klip disimpan di `dataset/<bahasa>/<kata>/`. Kata yang klipnya kurang dari 5 dilewati saat melatih.
Dari terminal (di folder project) juga bisa: `.venv/bin/python record.py id 30` merekam kata-kata di daftar `WORDS` dalam `record.py`, lalu `.venv/bin/python train.py id 50` untuk melatih.

Akurasi model dengan rekaman asli belum dites. Dengan ±30 klip per kata dari satu orang, biasanya cukup untuk demo beberapa kata, tapi jangan berharap andal untuk banyak kata atau orang lain.

## Yang perlu diketahui

1. **`train.py` dibuat baru**, karena file aslinya tidak ikut terkirim dari laptop Farid. Kalau ternyata Farid masih punya versinya, bandingkan dulu sebelum salah satunya ditimpa.
2. Teks kalimat cepat yang panjang (mis. "Saya butuh bantuan") terpotong di tombolnya. Hanya masalah tampilan.

## Yang sudah diubah dari versi Farid

Khusus Mac (di Windows kodenya tetap jalan seperti aslinya):

- `services.py`, suara: di macOS memakai perintah `say` (suara Damayanti untuk Indonesia, Samantha untuk English). Dengan pyttsx3 di Mac, kalimat baru memotong kalimat yang masih diucapkan, dan English malah memakai suara aneh "Albert".
- `services.py`, bunyi bip: `winsound` hanya ada di Windows. Di macOS nadanya sama (1000/1800 Hz, 130 ms) dan diputar lewat `afplay`.
- `main.py`, kamera: kalau kamera belum terbuka, aplikasi mencoba membukanya lagi tiap 3 detik. Di macOS kamera baru bisa dibuka setelah izin diberikan.

Untuk semua OS:

- Nama aplikasi: AksesKita → **SenseBridge** (judul jendela, sidebar, dan launcher).
- `train.py` (baru): melatih model bibir dari klip rekaman, dipakai tombol **Latih model** dan `run.py`.
- `services.py`, mikrofon Tuna Rungu: isi `SpeechListener._run` sebelumnya ternyata salinan kode suara keluar, jadi tombol mikrofon tidak berbuat apa-apa (di Windows juga). Sekarang ditulis ulang memakai `sounddevice`: kalibrasi bising ruangan 1 detik, bar volume, peringatan suara keras, lalu ucapan dipotong per kalimat dan dikirim ke Google Speech lewat fungsi `_recognize` milik Farid. `pyaudio` tidak diperlukan lagi.
- `main.py`: bar volume Tuna Rungu kembali ke 0 setelah tombol Berhenti ditekan, dan kotak LOG di Latih Model membungkus teks per kata.
- `tests/`: tes otomatis untuk mikrofon dan pelatihan model, memakai mikrofon, Google, dan klip bibir palsu. Jalankan dari folder project dengan `.venv/bin/python -m unittest discover tests`. Perintah `python` saja hanya ada kalau venv sudah aktif (misalnya di terminal VSCode setelah folder project dibuka).
- File baru lain: `README.md`, `requirements.txt`, `.gitignore`, `.vscode/settings.json`, `.vscode/launch.json`, `site/` (halaman proyek di Vercel), dan file ini.

Kalau folder ini dikirim ke orang lain, **jangan ikutkan `.venv/`** (±1,6 GB dan khusus Mac). Di laptopnya cukup `pip install -r requirements.txt`.

## Setup ulang (kalau `.venv` rusak atau pindah ke Mac lain)

Dari folder project:

```bash
rm -rf .venv
uv venv --python 3.12 --seed .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

## Kalau ada masalah

- **Kamera hitam terus**: buka System Settings → Privacy & Security → Camera, lalu nyalakan Visual Studio Code (atau Terminal). Tutup juga aplikasi lain yang sedang memakai kamera (Zoom, FaceTime, Photo Booth).
- **Yang terpakai malah kamera iPhone**: itu fitur Continuity Camera. Jauhkan iPhone atau matikan Continuity Camera di iPhone.
- **Suara tidak keluar**: cek volume Mac dan pastikan switch "Peringatan suara" di halaman Tuna Netra menyala.
- **Tuna Rungu menampilkan "tidak ada suara masuk, cek izin mikrofon"**: buka System Settings → Privacy & Security → Microphone, nyalakan Visual Studio Code (atau Terminal), lalu klik Berhenti dan Aktifkan mikrofon lagi.
- **Tuna Rungu: ucapan tidak jadi teks**: pengenalan suaranya memakai Google, jadi butuh internet. Kalau statusnya menyebut `Bad CPU type`, Mac itu belum punya Rosetta (encoder FLAC bawaan SpeechRecognition masih versi Intel). Pasang dengan `softwareupdate --install-rosetta`.
- **Latih model menampilkan "Error: butuh minimal 2 kata…"**: rekam lagi sampai minimal 2 kata (termasuk `_diam`) punya 5+ klip; idealnya ±30.
- **Baca bibir sering salah**: tambah klip per kata, rekam dengan cahaya dan posisi yang mirip saat dipakai, naikkan Epoch, atau naikkan "Ambang keyakinan" di Tuna Wicara supaya tebakan yang ragu tidak ditampilkan.
