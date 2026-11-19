"""strings.py - teks UI dua bahasa"""

TXT = {
    "id": {
        "app_sub": "Alat bantu aksesibilitas", "lang_label": "Bahasa",
        "big_text": "Teks besar", "dark_mode": "Mode gelap",
        "nav_netra": "Tuna Netra", "nav_rungu": "Tuna Rungu",
        "nav_wicara": "Tuna Wicara", "nav_latih": "Latih Model",
        "start": "Mulai", "stop": "Berhenti",
        # netra
        "netra_title": "Tuna Netra", "netra_sub": "Kamera mendeteksi hambatan di depan",
        "voice_warn": "Peringatan suara", "beep": "Bunyi bip",
        "sens": "Sensitivitas jarak", "idle": "Tekan Mulai untuk mengaktifkan kamera",
        "lvl_safe": "AMAN", "lvl_caution": "HATI-HATI", "lvl_danger": "BAHAYA",
        "path_clear": "Jalur di depan aman",
        "need_ultra": "Paket 'ultralytics' belum terpasang. Jalankan: pip install ultralytics",
        "loading_model": "Memuat model deteksi (pertama kali perlu internet)...",
        "disclaimer": "Alat bantu tambahan, bukan pengganti tongkat atau pendamping. "
                      "Jarak hanya perkiraan; tangga, lubang, dan kaca tidak terdeteksi.",
        # rungu
        "rungu_title": "Tuna Rungu", "rungu_sub": "Suara dan bibir diubah menjadi teks",
        "live_caption": "TEKS LANGSUNG", "history": "RIWAYAT", "mic_on": "Aktifkan mikrofon",
        "waiting": "Menunggu suara...", "lips_label": "Bibir",
        "calibrating": "Mengkalibrasi mikrofon, diam sebentar...",
        "listening": "Mendengarkan...", "loud_alert": "⚠ SUARA KERAS TERDETEKSI!",
        "err_net": "Tidak ada internet untuk pengenalan suara.",
        "err_mic": "Masalah mikrofon:",
        # wicara
        "wicara_title": "Tuna Wicara", "wicara_sub": "Bibir atau ketikan menjadi suara",
        "thr": "Ambang keyakinan", "compose": "PESAN", "speak": "🔊  Ucapkan",
        "undo_word": "Hapus kata", "clear": "Bersihkan",
        "auto_speak": "Ucapkan otomatis tiap kata dari bibir", "quick": "KALIMAT CEPAT",
        "no_face": "Wajah tidak terdeteksi", "mouth_open": "Mulut terbuka",
        "mouth_closed": "Mulut tertutup",
        "no_model": "Model bibir belum ada. Buka Latih Model.",
        # latih
        "latih_title": "Latih Model", "latih_sub": "Rekam kata lalu latih model bibir",
        "tips": "Rekam ±30 klip per kata dan kelas _diam (mulut diam). "
                "Mulai dengan 5-8 kata. Ucapkan kata selama 1 detik setelah hitung mundur.",
        "word": "KATA", "rec": "⏺  Rekam klip", "dataset": "DATASET", "log": "LOG",
        "epochs": "Epoch", "train": "Latih model", "model_ready": "Model siap dipakai",
        "model_none": "Belum ada model", "need_word": "Pilih atau ketik kata dulu.",
        "saved": "Tersimpan",
    },
    "en": {
        "app_sub": "Accessibility assistant", "lang_label": "Language",
        "big_text": "Large text", "dark_mode": "Dark mode",
        "nav_netra": "Visually Impaired", "nav_rungu": "Deaf",
        "nav_wicara": "Speech Impaired", "nav_latih": "Train Model",
        "start": "Start", "stop": "Stop",
        "netra_title": "Visually Impaired", "netra_sub": "Camera detects obstacles ahead",
        "voice_warn": "Voice warnings", "beep": "Beep sound",
        "sens": "Distance sensitivity", "idle": "Press Start to turn on the camera",
        "lvl_safe": "SAFE", "lvl_caution": "CAUTION", "lvl_danger": "DANGER",
        "path_clear": "Path ahead is clear",
        "need_ultra": "Package 'ultralytics' is missing. Run: pip install ultralytics",
        "loading_model": "Loading detection model (needs internet the first time)...",
        "disclaimer": "An extra aid, not a replacement for a cane or a guide. "
                      "Distance is an estimate; stairs, holes and glass are not detected.",
        "rungu_title": "Deaf", "rungu_sub": "Sound and lips turned into text",
        "live_caption": "LIVE CAPTION", "history": "HISTORY", "mic_on": "Turn on microphone",
        "waiting": "Waiting for sound...", "lips_label": "Lips",
        "calibrating": "Calibrating microphone, stay quiet for a moment...",
        "listening": "Listening...", "loud_alert": "⚠ LOUD SOUND DETECTED!",
        "err_net": "No internet connection for speech recognition.",
        "err_mic": "Microphone problem:",
        "wicara_title": "Speech Impaired", "wicara_sub": "Lips or typing turned into voice",
        "thr": "Confidence threshold", "compose": "MESSAGE", "speak": "🔊  Speak",
        "undo_word": "Undo word", "clear": "Clear",
        "auto_speak": "Speak each lip-read word automatically", "quick": "QUICK PHRASES",
        "no_face": "No face detected", "mouth_open": "Mouth open",
        "mouth_closed": "Mouth closed",
        "no_model": "No lip model yet. Open Train Model.",
        "latih_title": "Train Model", "latih_sub": "Record words, then train the lip model",
        "tips": "Record ~30 clips per word and the _diam class (silent mouth). "
                "Start with 5-8 words. Say the word for 1 second after the countdown.",
        "word": "WORD", "rec": "⏺  Record clip", "dataset": "DATASET", "log": "LOG",
        "epochs": "Epochs", "train": "Train model", "model_ready": "Model ready",
        "model_none": "No model yet", "need_word": "Pick or type a word first.",
        "saved": "Saved",
    },
}

QUICK = {
    "id": ["Halo", "Terima kasih", "Tolong", "Ya", "Tidak", "Maaf",
           "Saya butuh bantuan", "Di mana toilet?"],
    "en": ["Hello", "Thank you", "Please help", "Yes", "No", "Sorry",
           "I need assistance", "Where is the restroom?"],
}

SUGGEST = {
    "id": ["_diam", "tolong", "makan", "minum", "air", "ya", "tidak", "halo"],
    "en": ["_diam", "help", "eat", "drink", "water", "yes", "no", "hello"],
}