"""Launcher SenseBridge: cek Python, file, dan library sebelum menjalankan main.py"""
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

REQUIRED_FILES = ["main.py", "services.py", "strings.py", "lipcore.py", "train.py"]

# nama modul -> nama paket pip
REQUIRED_PACKAGES = {
    "customtkinter": "customtkinter",
    "cv2": "opencv-python",
    "numpy": "numpy",
    "mediapipe": "mediapipe==0.10.14",
    "PIL": "pillow",
    "torch": "torch",
    "pyttsx3": "pyttsx3",
    "speech_recognition": "SpeechRecognition",
    "ultralytics": "ultralytics",
}


def check_python():
    v = sys.version_info
    print(f"Python  : {sys.version.split()[0]}  ({sys.executable})")
    if v >= (3, 13):
        print("\n[X] Python terlalu baru. mediapipe butuh Python 3.11 atau 3.12.")
        print("    Buat ulang venv:  py -3.11 -m venv venv")
        sys.exit(1)


def check_files():
    missing = [f for f in REQUIRED_FILES if not os.path.exists(os.path.join(HERE, f))]
    if missing:
        print("\n[X] File berikut tidak ditemukan di", HERE)
        for f in missing:
            print("    -", f)
        print("\nPastikan main.py, services.py, strings.py dipisah jadi 3 file")
        print("(jangan digabung dalam satu file seperti test.py).")
        sys.exit(1)

    # deteksi file gabungan (main.py yang isinya berisi kode services/strings)
    with open(os.path.join(HERE, "main.py"), encoding="utf-8") as f:
        text = f.read()
    if text.count("import customtkinter") > 1 or "def speak" in text and "class " in text and "STRINGS" in text and "def tr(" in text:
        print("[!] main.py sepertinya berisi gabungan file lain. Cek lagi.")


def check_packages():
    missing = [pip for mod, pip in REQUIRED_PACKAGES.items()
               if importlib.util.find_spec(mod) is None]
    if not missing:
        print("Library : semua terpasang")
        return
    print("\n[!] Library belum terpasang:")
    for m in missing:
        print("    -", m)
    jawab = input("\nPasang sekarang? (y/n): ").strip().lower()
    if jawab != "y":
        print("Perintah manual:\n  " + sys.executable + " -m pip install " + " ".join(missing))
        sys.exit(1)
    # pakai interpreter yang sama dengan yang menjalankan skrip ini
    cmd = [sys.executable, "-m", "pip", "install", *missing]
    if subprocess.call(cmd) != 0:
        print("\n[X] Instalasi gagal. Kirim teks errornya.")
        sys.exit(1)
    print("\nInstalasi selesai. Jalankan run.py lagi.")
    sys.exit(0)


def main():
    check_python()
    check_files()
    check_packages()
    print("\nMenjalankan SenseBridge...\n")
    import runpy
    runpy.run_path(os.path.join(HERE, "main.py"), run_name="__main__")


if __name__ == "__main__":
    main()