// Interface text in Indonesian (default) and English.
// Ported from Farid's strings.py (TXT, QUICK, SUGGEST) and services.py
// (NAMES_ID, DIR), plus the text only the web version needs.

export const STRINGS = {
  id: {
    app_sub: "Alat bantu aksesibilitas", lang_label: "Bahasa",
    big_text: "Teks besar", dark_mode: "Mode gelap",
    nav_netra: "Tuna Netra", nav_rungu: "Tuna Rungu",
    nav_wicara: "Tuna Wicara", nav_latih: "Latih Model",
    start: "Mulai", stop: "Berhenti",
    // netra
    netra_title: "Tuna Netra", netra_sub: "Kamera mendeteksi hambatan di depan",
    voice_warn: "Peringatan suara", beep: "Bunyi bip",
    sens: "Sensitivitas jarak", idle: "Tekan Mulai untuk mengaktifkan kamera",
    lvl_safe: "AMAN", lvl_caution: "HATI-HATI", lvl_danger: "BAHAYA",
    path_clear: "Jalur di depan aman",
    loading_model: "Memuat model deteksi (pertama kali sekitar 18 MB)...",
    disclaimer: "Alat bantu tambahan, bukan pengganti tongkat atau pendamping. " +
      "Jarak hanya perkiraan; tangga, lubang, dan kaca tidak terdeteksi.",
    // rungu
    rungu_title: "Tuna Rungu", rungu_sub: "Suara dan bibir diubah menjadi teks",
    live_caption: "TEKS LANGSUNG", history: "RIWAYAT", mic_on: "Aktifkan mikrofon",
    waiting: "Menunggu suara...", lips_label: "Bibir",
    listening: "Mendengarkan...", loud_alert: "SUARA KERAS TERDETEKSI!",
    err_net: "Tidak ada internet untuk pengenalan suara.",
    // wicara
    wicara_title: "Tuna Wicara", wicara_sub: "Bibir atau ketikan menjadi suara",
    thr: "Ambang keyakinan", compose: "PESAN", speak: "Ucapkan",
    undo_word: "Hapus kata", clear: "Bersihkan",
    auto_speak: "Ucapkan otomatis tiap kata dari bibir", quick: "KALIMAT CEPAT",
    no_face: "Wajah tidak terdeteksi", mouth_open: "Mulut terbuka",
    mouth_closed: "Mulut tertutup",
    no_model: "Model bibir belum ada. Buka Latih Model.",
    // latih
    latih_title: "Latih Model", latih_sub: "Rekam kata lalu latih model bibir",
    tips: "Rekam ±30 klip per kata dan kelas _diam (mulut diam). " +
      "Mulai dengan 5-8 kata. Ucapkan kata selama 1 detik setelah hitung mundur.",
    word: "KATA", rec: "Rekam klip", dataset: "DATASET", log: "LOG",
    epochs: "Epoch", train: "Latih model", model_ready: "Model siap dipakai",
    model_none: "Belum ada model", need_word: "Pilih atau ketik kata dulu.",
    saved: "Tersimpan",
    // web only
    about: "Tentang",
    skip: "Langsung ke isi",
    home_title: "Pilih jalur",
    home_lede: "Satu indra masuk, indra lain keluar. Kamera dan mikrofon dipakai langsung di perangkat ini.",
    all_lines: "Semua jalur",
    line_netra_from: "Kamera melihat jalan", line_netra_to: "Kamu mendengar peringatan",
    line_rungu_from: "Mikrofon mendengar ucapan", line_rungu_to: "Kamu membaca teks besar",
    line_wicara_from: "Bibir bergerak, jari mengetik", line_wicara_to: "Orang lain mendengar suaramu",
    line_latih_from: "Kamu merekam kata", line_latih_to: "Model bibirmu sendiri",
    note_privacy: "Gambar kamera dan suara mikrofon tidak disimpan.",
    note_browser: "Teks dari suara butuh Chrome, Edge, atau Safari dan internet.",
    netra_started: "Deteksi dimulai",
    zone_left: "Kiri", zone_center: "Depan", zone_right: "Kanan",
    model_failed: "Model deteksi gagal dimuat. Cek internet, lalu tekan Mulai lagi.",
    perm_camera: "Izin kamera ditolak. Izinkan kamera untuk situs ini di pengaturan browser, lalu tekan Mulai lagi.",
    no_camera: "Kamera tidak ditemukan.",
    cam_busy: "Kamera sedang dipakai aplikasi lain.",
    cam_error: "Kamera tidak bisa dibuka.",
    perm_mic: "Izin mikrofon ditolak. Izinkan mikrofon untuk situs ini di pengaturan browser.",
    no_mic: "Mikrofon tidak ditemukan.",
    mic_busy: "Mikrofon sedang dipakai aplikasi lain.",
    mic_error: "Mikrofon tidak bisa dibuka.",
    no_speech_api: "Browser ini belum bisa mengubah suara jadi teks. Pakai Chrome, Edge, atau Safari. Peringatan suara keras tetap jalan.",
    lang_unsupported: "Bahasa ini belum didukung pengenal suara di browser ini.",
    rungu_note: "Teks dibuat oleh pengenal suara bawaan browser (Google di Chrome, Microsoft di Edge, Apple di Safari), jadi butuh internet.",
    meter_off: "Peringatan suara keras dimatikan supaya teks tetap jalan di perangkat ini.",
    speech_denied: "Pengenal suara ditolak. Izinkan pengenalan suara (Dikte) untuk browser ini di pengaturan. Peringatan suara keras tetap jalan.",
    msg_placeholder: "Ketik pesan di sini",
    lips_soon: "Baca bibir menyusul di tahap berikutnya.",
    latih_soon: "Latih Model sedang dibuat. Sementara ini, rekam dan latih model bibir di versi Python.",
  },
  en: {
    app_sub: "Accessibility assistant", lang_label: "Language",
    big_text: "Large text", dark_mode: "Dark mode",
    nav_netra: "Visually Impaired", nav_rungu: "Deaf",
    nav_wicara: "Speech Impaired", nav_latih: "Train Model",
    start: "Start", stop: "Stop",
    netra_title: "Visually Impaired", netra_sub: "Camera detects obstacles ahead",
    voice_warn: "Voice warnings", beep: "Beep sound",
    sens: "Distance sensitivity", idle: "Press Start to turn on the camera",
    lvl_safe: "SAFE", lvl_caution: "CAUTION", lvl_danger: "DANGER",
    path_clear: "Path ahead is clear",
    loading_model: "Loading the detection model (about 18 MB the first time)...",
    disclaimer: "An extra aid, not a replacement for a cane or a guide. " +
      "Distance is an estimate; stairs, holes and glass are not detected.",
    rungu_title: "Deaf", rungu_sub: "Sound and lips turned into text",
    live_caption: "LIVE CAPTION", history: "HISTORY", mic_on: "Turn on microphone",
    waiting: "Waiting for sound...", lips_label: "Lips",
    listening: "Listening...", loud_alert: "LOUD SOUND DETECTED!",
    err_net: "No internet connection for speech recognition.",
    wicara_title: "Speech Impaired", wicara_sub: "Lips or typing turned into voice",
    thr: "Confidence threshold", compose: "MESSAGE", speak: "Speak",
    undo_word: "Undo word", clear: "Clear",
    auto_speak: "Speak each lip-read word automatically", quick: "QUICK PHRASES",
    no_face: "No face detected", mouth_open: "Mouth open",
    mouth_closed: "Mouth closed",
    no_model: "No lip model yet. Open Train Model.",
    latih_title: "Train Model", latih_sub: "Record words, then train the lip model",
    tips: "Record ~30 clips per word and the _diam class (silent mouth). " +
      "Start with 5-8 words. Say the word for 1 second after the countdown.",
    word: "WORD", rec: "Record clip", dataset: "DATASET", log: "LOG",
    epochs: "Epochs", train: "Train model", model_ready: "Model ready",
    model_none: "No model yet", need_word: "Pick or type a word first.",
    saved: "Saved",
    about: "About",
    skip: "Skip to content",
    home_title: "Choose a line",
    home_lede: "One sense in, another sense out. The camera and microphone are used right here on this device.",
    all_lines: "All lines",
    line_netra_from: "The camera sees the way", line_netra_to: "You hear a warning",
    line_rungu_from: "The microphone hears speech", line_rungu_to: "You read large captions",
    line_wicara_from: "Lips move, keys type", line_wicara_to: "Others hear your words",
    line_latih_from: "You record a word", line_latih_to: "Your own lip model",
    note_privacy: "Camera images and microphone sound are not stored.",
    note_browser: "Captions need Chrome, Edge or Safari and an internet connection.",
    netra_started: "Detection started",
    zone_left: "Left", zone_center: "Ahead", zone_right: "Right",
    model_failed: "The detection model did not load. Check the internet, then press Start again.",
    perm_camera: "Camera permission was denied. Allow the camera for this site in the browser settings, then press Start again.",
    no_camera: "No camera found.",
    cam_busy: "The camera is being used by another app.",
    cam_error: "The camera could not be opened.",
    perm_mic: "Microphone permission was denied. Allow the microphone for this site in the browser settings.",
    no_mic: "No microphone found.",
    mic_busy: "The microphone is being used by another app.",
    mic_error: "The microphone could not be opened.",
    no_speech_api: "This browser cannot turn speech into text yet. Use Chrome, Edge or Safari. The loud-sound alert still works.",
    lang_unsupported: "This browser's speech recognition does not support this language.",
    rungu_note: "Captions come from the browser's own speech recognition (Google in Chrome, Microsoft in Edge, Apple in Safari), so they need the internet.",
    meter_off: "The loud-sound alert is turned off so captions can run on this device.",
    speech_denied: "Speech recognition was refused. Allow speech recognition (Dictation) for this browser in the settings. The loud-sound alert still works.",
    msg_placeholder: "Type your message here",
    lips_soon: "Lip reading comes in the next stage.",
    latih_soon: "Train Model is being built. For now, record and train the lip model in the Python version.",
  },
};

export const QUICK = {
  id: ["Halo", "Terima kasih", "Tolong", "Ya", "Tidak", "Maaf",
    "Saya butuh bantuan", "Di mana toilet?"],
  en: ["Hello", "Thank you", "Please help", "Yes", "No", "Sorry",
    "I need assistance", "Where is the restroom?"],
};

export const SUGGEST = {
  id: ["_diam", "tolong", "makan", "minum", "air", "ya", "tidak", "halo"],
  en: ["_diam", "help", "eat", "drink", "water", "yes", "no", "hello"],
};

// Detector class names (COCO) to the Indonesian words Farid's app speaks.
export const NAMES_ID = {
  "person": "orang", "chair": "kursi", "couch": "sofa", "bed": "tempat tidur",
  "dining table": "meja", "car": "mobil", "motorcycle": "motor",
  "bicycle": "sepeda", "bus": "bus", "truck": "truk", "dog": "anjing",
  "cat": "kucing", "bench": "bangku", "potted plant": "tanaman",
  "tv": "televisi", "laptop": "laptop", "bottle": "botol", "backpack": "tas",
  "suitcase": "koper", "toilet": "toilet", "refrigerator": "kulkas",
  "fire hydrant": "hidran", "stop sign": "rambu berhenti",
};

export const DIR = {
  id: { left: "kiri", center: "depan", right: "kanan" },
  en: { left: "on the left", center: "ahead", right: "on the right" },
};

// Text for `key` in `lang`; falls back to Indonesian, then to the key itself.
export function t(lang, key) {
  const table = Object.hasOwn(STRINGS, lang) ? STRINGS[lang] : STRINGS.id;
  if (Object.hasOwn(table, key)) return table[key];
  if (Object.hasOwn(STRINGS.id, key)) return STRINGS.id[key];
  return key;
}
