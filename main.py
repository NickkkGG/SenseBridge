"""SenseBridge - alat bantu aksesibilitas (Indonesia + English)

  Tuna Netra   : kamera deteksi hambatan -> peringatan suara + visual
  Tuna Rungu   : mikrofon + bibir -> teks besar di layar, peringatan suara keras
  Tuna Wicara  : bibir / ketikan -> teks -> diucapkan lewat speaker
  Latih Model  : rekam kata + latih model bibir per bahasa

Jalankan:  python main.py
"""
import queue
import threading
import time
import tkinter as tk
from datetime import datetime

import cv2
import customtkinter as ctk
from PIL import Image, ImageTk

import lipcore as lc
import services
import strings as S

ctk.set_default_color_theme("blue")

C = {
    "bg": ("#F2F3F7", "#0E1016"), "card": ("#FFFFFF", "#181B25"),
    "side": ("#E7E9F0", "#12141C"), "text": ("#14161C", "#F2F4F8"),
    "sub": ("#6B7080", "#9AA0B4"), "idle": ("#D5D8E2", "#2A2E3D"),
    "field": ("#F0F1F6", "#222635"),
    "ok": "#2ECC71", "warn": "#F5A623", "bad": "#FF4D4F",
    "netra": "#FF8A3D", "rungu": "#4F8CFF", "wicara": "#8B5CF6", "latih": "#2ECC71",
}


def card(parent, **kw):
    return ctk.CTkFrame(parent, corner_radius=20, fg_color=C["card"], **kw)


class CamView(tk.Label):
    """Label biasa (lebih ringan dari CTkLabel untuk video)."""

    def __init__(self, parent, w, h):
        super().__init__(parent, bg="#05070B", bd=0)
        self.w, self.h, self._ph = w, h, None

    def show(self, bgr):
        rgb = cv2.cvtColor(cv2.resize(bgr, (self.w, self.h)), cv2.COLOR_BGR2RGB)
        self._ph = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.configure(image=self._ph)


class BasePage(ctk.CTkFrame):
    needs_face = False
    accent = "#4F8CFF"

    def __init__(self, app, parent):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._tx = []

    def reg(self, widget, key):
        self._tx.append((widget, key))
        widget.configure(text=self.app.t(key))
        return widget

    def retext(self):
        for w, k in self._tx:
            w.configure(text=self.app.t(k))

    def header(self, title_key, sub_key):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=0, column=0, columnspan=2, sticky="ew")
        ctk.CTkFrame(f, width=8, height=44, corner_radius=4,
                     fg_color=self.accent).pack(side="left", padx=(0, 14))
        box = ctk.CTkFrame(f, fg_color="transparent")
        box.pack(side="left")
        t = self.reg(ctk.CTkLabel(box, text="", font=self.app.f_title,
                                  anchor="w"), title_key)
        t.pack(anchor="w")
        s = self.reg(ctk.CTkLabel(box, text="", font=self.app.f_sub, anchor="w",
                                  text_color=C["sub"]), sub_key)
        s.pack(anchor="w")

    def on_show(self): pass
    def on_hide(self): pass
    def on_frame(self, frame, roi, lm): pass
    def on_event(self, kind, payload): pass
    def on_lang(self): pass


# ============================ TUNA NETRA ============================
class BlindPage(BasePage):
    needs_face = False
    accent = C["netra"]

    def __init__(self, app, parent):
        super().__init__(app, parent)
        self.running, self.n = False, 0
        self.last_msg, self.last_t = "", 0.0
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self.header("netra_title", "netra_sub")

        left = card(self)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(14, 0))
        self.cam = CamView(left, 640, 480)
        self.cam.pack(padx=14, pady=(14, 8))
        zr = ctk.CTkFrame(left, fg_color="transparent")
        zr.pack(fill="x", padx=14, pady=(0, 14))
        self.zones = {}
        for i, z in enumerate(("left", "center", "right")):
            zr.grid_columnconfigure(i, weight=1)
            f = ctk.CTkFrame(zr, height=16, corner_radius=8, fg_color=C["idle"])
            f.grid(row=0, column=i, sticky="ew", padx=4)
            self.zones[z] = f

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", pady=(14, 0))
        self.status = card(right)
        self.status.pack(fill="x")
        self.lvl = ctk.CTkLabel(self.status, text="—", font=app.f_huge)
        self.lvl.pack(pady=(26, 4))
        self.msg = ctk.CTkLabel(self.status, text="", font=app.f_body,
                                wraplength=340, justify="center")
        self.msg.pack(padx=16, pady=(0, 26))

        self.btn = ctk.CTkButton(right, height=56, corner_radius=16,
                                 font=app.f_btn, fg_color=self.accent,
                                 hover_color="#E5762B", command=self.toggle)
        self.btn.pack(fill="x", pady=14)

        opts = card(right)
        opts.pack(fill="x")
        self.voice = tk.BooleanVar(value=True)
        self.beepv = tk.BooleanVar(value=True)
        self.sens = tk.DoubleVar(value=1.0)
        self.reg(ctk.CTkSwitch(opts, text="", variable=self.voice, onvalue=True,
                               offvalue=False, progress_color=self.accent,
                               font=app.f_body), "voice_warn").pack(
            anchor="w", padx=18, pady=(16, 6))
        self.reg(ctk.CTkSwitch(opts, text="", variable=self.beepv, onvalue=True,
                               offvalue=False, progress_color=self.accent,
                               font=app.f_body), "beep").pack(
            anchor="w", padx=18, pady=6)
        self.reg(ctk.CTkLabel(opts, text="", font=app.f_small,
                              text_color=C["sub"]), "sens").pack(
            anchor="w", padx=18, pady=(10, 0))
        ctk.CTkSlider(opts, from_=0.6, to=1.6, variable=self.sens,
                      progress_color=self.accent).pack(
            fill="x", padx=18, pady=(4, 16))

        self.reg(ctk.CTkLabel(right, text="", font=app.f_small,
                              text_color=C["sub"], wraplength=360,
                              justify="left"), "disclaimer").pack(
            anchor="w", pady=12)
        self.reset_ui()
        self.refresh_btn()

    def refresh_btn(self):
        self.btn.configure(
            text=self.app.t("stop" if self.running else "start"),
            fg_color=C["bad"] if self.running else self.accent)

    def retext(self):
        super().retext()
        self.refresh_btn()
        if not self.running:
            self.reset_ui()

    def reset_ui(self):
        self.status.configure(fg_color=C["card"])
        self.lvl.configure(text="—", text_color=C["text"])
        self.msg.configure(text=self.app.t("idle"), text_color=C["sub"])
        for f in self.zones.values():
            f.configure(fg_color=C["idle"])

    def toggle(self):
        self.running = not self.running
        if self.running:
            self.app.detector.start()
        else:
            self.reset_ui()
        self.refresh_btn()

    def on_hide(self):
        if self.running:
            self.toggle()

    def set_level(self, level, text, zone):
        col = [C["ok"], C["warn"], C["bad"]][level]
        names = ["lvl_safe", "lvl_caution", "lvl_danger"]
        self.status.configure(fg_color=col)
        self.lvl.configure(text=self.app.t(names[level]), text_color="white")
        self.msg.configure(text=text or self.app.t("path_clear"),
                           text_color="white")
        for z, f in self.zones.items():
            f.configure(fg_color=col if (z == zone and level) else C["idle"])

    def alert(self, level, text):
        if level == 0:
            return
        now = time.time()
        cool = 2.0 if level == 2 else 4.0
        if (text != self.last_msg or now - self.last_t > cool) \
                and now - self.last_t > 1.2:
            self.last_msg, self.last_t = text, now
            if self.voice.get():
                self.app.speaker.say(text, self.app.lang, interrupt=(level == 2))
            if self.beepv.get():
                self.app.speaker.beep(level)

    def on_frame(self, frame, roi, lm):
        if self.running:
            det = self.app.detector
            H, W = frame.shape[:2]
            if det.error:
                msg = self.app.t("need_ultra") if det.error == "ultralytics" \
                    else det.error
                self.msg.configure(text=msg, text_color=C["bad"])
            elif not det.ready:
                self.msg.configure(text=self.app.t("loading_model"),
                                   text_color=C["sub"])
            else:
                self.n += 1
                if self.n % 2 == 0:
                    det.submit(frame.copy())
                dets, t = det.result
                if time.time() - t < 1.0:
                    lvl, text, zone, _ = services.assess(
                        dets, W, H, self.app.lang, self.sens.get())
                    self.draw(frame, dets, W, H)
                    self.set_level(lvl, text, zone)
                    self.alert(lvl, text)
        self.cam.show(frame)

    def draw(self, frame, dets, W, H):
        for name, conf, x1, y1, x2, y2 in dets:
            hr = (y2 - y1) / H * self.sens.get()
            col = (77, 77, 255) if hr >= 0.65 else (35, 166, 245) \
                if hr >= 0.40 else (160, 160, 160)
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), col, 3)
            cv2.putText(frame, name, (int(x1) + 4, int(y1) + 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)


# ============================ TUNA RUNGU ============================
class DeafPage(BasePage):
    needs_face = True
    accent = C["rungu"]

    def __init__(self, app, parent):
        super().__init__(app, parent)
        self.on, self.flash_id = False, None
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self.header("rungu_title", "rungu_sub")

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(14, 0))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        cap = card(left)
        cap.grid(row=0, column=0, sticky="ew")
        self.reg(ctk.CTkLabel(cap, text="", font=app.f_small,
                              text_color=C["sub"]), "live_caption").pack(
            anchor="w", padx=20, pady=(14, 0))
        self.caption = ctk.CTkLabel(cap, text="", font=app.f_caption,
                                    wraplength=620, justify="left", anchor="w",
                                    height=190)
        self.caption.pack(fill="x", padx=20, pady=(4, 8))
        self.banner = ctk.CTkLabel(cap, text="", font=app.f_btn, height=36,
                                   corner_radius=10, text_color="white")
        self.banner.pack(fill="x", padx=20, pady=(0, 6))
        self.vol = ctk.CTkProgressBar(cap, height=12, progress_color=self.accent)
        self.vol.set(0)
        self.vol.pack(fill="x", padx=20, pady=(0, 16))

        hist = card(left)
        hist.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self.reg(ctk.CTkLabel(hist, text="", font=app.f_small,
                              text_color=C["sub"]), "history").pack(
            anchor="w", padx=20, pady=(12, 0))
        self.hist = ctk.CTkTextbox(hist, font=app.f_body, fg_color="transparent",
                                   wrap="word", state="disabled")
        self.hist.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", pady=(14, 0))
        cc = card(right)
        cc.pack(fill="x")
        self.cam = CamView(cc, 380, 285)
        self.cam.pack(padx=12, pady=12)
        self.lipchip = ctk.CTkLabel(right, text="", font=app.f_body,
                                    fg_color=C["card"], corner_radius=14,
                                    height=46)
        self.lipchip.pack(fill="x", pady=12)
        self.btn = ctk.CTkButton(right, height=56, corner_radius=16,
                                 font=app.f_btn, fg_color=self.accent,
                                 hover_color="#3A74E0", command=self.toggle)
        self.btn.pack(fill="x")
        self.status = ctk.CTkLabel(right, text="", font=app.f_small,
                                   text_color=C["sub"], wraplength=360)
        self.status.pack(pady=10)
        self.retext()
        self.banner.configure(fg_color="transparent")

    def retext(self):
        super().retext()
        self.btn.configure(text=self.app.t("stop" if self.on else "mic_on"),
                           fg_color=C["bad"] if self.on else self.accent)
        if not self.caption.cget("text"):
            self.caption.configure(text=self.app.t("waiting"),
                                   text_color=C["sub"])
        self.lipchip.configure(text=f"👄  {self.app.t('lips_label')}: —",
                               text_color=C["sub"])

    def toggle(self):
        self.on = not self.on
        if self.on:
            self.app.listener.start()
            self.status.configure(text=self.app.t("calibrating"),
                                  text_color=C["sub"])
        else:
            self.app.listener.stop()
            self.vol.set(0)
            self.status.configure(text="")
        self.btn.configure(text=self.app.t("stop" if self.on else "mic_on"),
                           fg_color=C["bad"] if self.on else self.accent)

    def on_hide(self):
        if self.on:
            self.toggle()

    def log(self, line):
        self.hist.configure(state="normal")
        self.hist.insert("end", f"[{datetime.now():%H:%M:%S}] {line}\n")
        self.hist.see("end")
        self.hist.configure(state="disabled")

    def on_event(self, kind, p):
        if kind == "level" and self.on:      # abaikan level yang masih antre setelah Berhenti
            self.vol.set(p)
        elif kind == "speech":
            self.caption.configure(text=p, text_color=C["text"])
            self.log(f"🎙 {p}")
        elif kind == "alert":
            self.banner.configure(text=self.app.t("loud_alert"),
                                  fg_color=C["bad"])
            if self.flash_id:
                self.after_cancel(self.flash_id)
            self.flash_id = self.after(
                3000, lambda: self.banner.configure(text="", fg_color="transparent"))
        elif kind == "mic" and self.on:
            if p == "ready":
                self.status.configure(text=self.app.t("listening"),
                                      text_color=C["ok"])
        elif kind == "stt_error":
            msg = self.app.t("err_net") if p == "net" else \
                f"{self.app.t('err_mic')} {p[4:]}"
            self.status.configure(text=msg, text_color=C["bad"])

    def on_frame(self, frame, roi, lm):
        app = self.app
        if roi is not None:
            app.lip.push(roi)
            res = app.lip.step(app.thr.get())
            if res:
                word, conf, new = res
                if word != lc.SILENCE and conf >= app.thr.get():
                    self.lipchip.configure(
                        text=f"👄  {app.t('lips_label')}: {word}  ({conf:.0%})",
                        text_color=C["text"])
                    if new:
                        self.log(f"👄 {word}")
                else:
                    self.lipchip.configure(
                        text=f"👄  {app.t('lips_label')}: …", text_color=C["sub"])
        else:
            app.lip.reset()
        self.cam.show(frame)


# ============================ TUNA WICARA ============================
class MutePage(BasePage):
    needs_face = True
    accent = C["wicara"]

    def __init__(self, app, parent):
        super().__init__(app, parent)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)
        self.header("wicara_title", "wicara_sub")

        left = card(self)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(14, 0))
        self.cam = CamView(left, 440, 330)
        self.cam.pack(padx=14, pady=14)
        self.badge = ctk.CTkLabel(left, text="", font=app.f_btn, height=44,
                                  corner_radius=14, fg_color=C["field"])
        self.badge.pack(fill="x", padx=14)
        self.lipchip = ctk.CTkLabel(left, text="", font=app.f_body, height=44,
                                    corner_radius=14, fg_color=C["field"])
        self.lipchip.pack(fill="x", padx=14, pady=10)
        self.reg(ctk.CTkLabel(left, text="", font=app.f_small,
                              text_color=C["sub"]), "thr").pack(
            anchor="w", padx=18)
        ctk.CTkSlider(left, from_=0.3, to=0.95, variable=app.thr,
                      progress_color=self.accent).pack(
            fill="x", padx=18, pady=(2, 16))

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", pady=(14, 0))
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        comp = card(right)
        comp.grid(row=0, column=0, sticky="nsew")
        self.reg(ctk.CTkLabel(comp, text="", font=app.f_small,
                              text_color=C["sub"]), "compose").pack(
            anchor="w", padx=20, pady=(14, 0))
        self.box = ctk.CTkTextbox(comp, font=app.f_caption_m, wrap="word",
                                  fg_color=C["field"], corner_radius=14)
        self.box.pack(fill="both", expand=True, padx=16, pady=10)
        row = ctk.CTkFrame(comp, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 8))
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure((1, 2), weight=1)
        self.b_speak = ctk.CTkButton(row, height=52, corner_radius=14,
                                     font=app.f_btn, fg_color=self.accent,
                                     hover_color="#7447D6", command=self.speak)
        self.b_speak.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.b_undo = ctk.CTkButton(row, height=52, corner_radius=14,
                                    font=app.f_btn, fg_color=C["field"],
                                    text_color=C["text"], hover_color=C["idle"],
                                    command=self.undo)
        self.b_undo.grid(row=0, column=1, sticky="ew", padx=4)
        self.b_clear = ctk.CTkButton(row, height=52, corner_radius=14,
                                     font=app.f_btn, fg_color=C["field"],
                                     text_color=C["text"], hover_color=C["idle"],
                                     command=self.clear)
        self.b_clear.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        self.auto = tk.BooleanVar(value=False)
        self.reg(ctk.CTkSwitch(comp, text="", variable=self.auto, onvalue=True,
                               offvalue=False, progress_color=self.accent,
                               font=app.f_small), "auto_speak").pack(
            anchor="w", padx=20, pady=(0, 14))

        qc = card(right)
        qc.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        self.reg(ctk.CTkLabel(qc, text="", font=app.f_small,
                              text_color=C["sub"]), "quick").pack(
            anchor="w", padx=20, pady=(12, 4))
        self.qbox = ctk.CTkFrame(qc, fg_color="transparent")
        self.qbox.pack(fill="x", padx=14, pady=(0, 14))
        self.build_quick()
        self.retext()

    def retext(self):
        super().retext()
        self.b_speak.configure(text=self.app.t("speak"))
        self.b_undo.configure(text=self.app.t("undo_word"))
        self.b_clear.configure(text=self.app.t("clear"))
        self.lipchip.configure(text="👄  …", text_color=C["sub"])

    def on_lang(self):
        self.build_quick()

    def build_quick(self):
        for w in self.qbox.winfo_children():
            w.destroy()
        for i, ph in enumerate(S.QUICK[self.app.lang]):
            self.qbox.grid_columnconfigure(i % 4, weight=1)
            ctk.CTkButton(self.qbox, text=ph, height=44, corner_radius=12,
                          font=self.app.f_body, fg_color=C["field"],
                          text_color=C["text"], hover_color=self.accent,
                          command=lambda p=ph: self.quick(p)).grid(
                row=i // 4, column=i % 4, sticky="ew", padx=4, pady=4)

    def quick(self, phrase):
        self.box.insert("end", phrase + " ")
        self.app.speaker.say(phrase, self.app.lang, interrupt=True)

    def speak(self):
        text = self.box.get("1.0", "end").strip()
        if text:
            self.app.speaker.say(text, self.app.lang, interrupt=True)

    def clear(self):
        self.box.delete("1.0", "end")

    def undo(self):
        words = self.box.get("1.0", "end").strip().split()
        self.box.delete("1.0", "end")
        self.box.insert("end", " ".join(words[:-1]) + (" " if len(words) > 1 else ""))

    def on_frame(self, frame, roi, lm):
        app = self.app
        H, W = frame.shape[:2]
        if roi is None or lm is None:
            app.lip.reset()
            self.badge.configure(text=app.t("no_face"), text_color=C["sub"])
        else:
            op = services.mouth_open_ratio(lm, W, H) > 0.08
            self.badge.configure(
                text=app.t("mouth_open" if op else "mouth_closed"),
                text_color=C["ok"] if op else C["sub"])
            app.lip.push(roi)
            if not app.lip.model:
                self.lipchip.configure(text=app.t("no_model"),
                                       text_color=C["warn"])
            else:
                res = app.lip.step(app.thr.get())
                if res:
                    word, conf, new = res
                    if word != lc.SILENCE and conf >= app.thr.get():
                        self.lipchip.configure(
                            text=f"👄  {word}  ({conf:.0%})",
                            text_color=C["text"])
                        if new:
                            self.box.insert("end", word + " ")
                            if self.auto.get():
                                app.speaker.say(word, app.lang)
                    else:
                        self.lipchip.configure(text="👄  …", text_color=C["sub"])
        self.cam.show(frame)


# ============================ LATIH MODEL ============================
class TrainPage(BasePage):
    needs_face = True
    accent = C["latih"]

    def __init__(self, app, parent):
        super().__init__(app, parent)
        self.rec, self.training, self.pending_roi = None, False, None
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)
        self.header("latih_title", "latih_sub")

        left = card(self)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(14, 0))
        self.cam = CamView(left, 440, 330)
        self.cam.pack(padx=14, pady=14)
        self.big = ctk.CTkLabel(left, text="…", font=app.f_huge)
        self.big.pack(pady=4)
        self.status = ctk.CTkLabel(left, text="", font=app.f_body,
                                   text_color=C["sub"], wraplength=400)
        self.status.pack(pady=4)
        self.reg(ctk.CTkLabel(left, text="", font=app.f_small,
                              text_color=C["sub"], wraplength=400,
                              justify="left"), "tips").pack(
            padx=16, pady=(6, 14))

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", pady=(14, 0))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        rc = card(right)
        rc.grid(row=0, column=0, sticky="ew")
        self.reg(ctk.CTkLabel(rc, text="", font=app.f_small,
                              text_color=C["sub"]), "word").pack(
            anchor="w", padx=20, pady=(14, 0))
        self.word = ctk.CTkComboBox(rc, values=[""], font=app.f_body,
                                    height=44, corner_radius=12,
                                    button_color=self.accent)
        self.word.pack(fill="x", padx=18, pady=6)
        self.btn_rec = ctk.CTkButton(rc, height=52, corner_radius=14,
                                     font=app.f_btn, fg_color=C["bad"],
                                     hover_color="#D93B3D", command=self.start_rec)
        self.btn_rec.pack(fill="x", padx=18, pady=(4, 16))

        mid = ctk.CTkFrame(right, fg_color="transparent")
        mid.grid(row=1, column=0, sticky="nsew", pady=12)
        mid.grid_columnconfigure((0, 1), weight=1)
        mid.grid_rowconfigure(0, weight=1)
        dc = card(mid)
        dc.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.reg(ctk.CTkLabel(dc, text="", font=app.f_small,
                              text_color=C["sub"]), "dataset").pack(
            anchor="w", padx=16, pady=(12, 0))
        self.counts = ctk.CTkTextbox(dc, font=app.f_body, fg_color="transparent",
                                     state="disabled")
        self.counts.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        lc_ = card(mid)
        lc_.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.reg(ctk.CTkLabel(lc_, text="", font=app.f_small,
                              text_color=C["sub"]), "log").pack(
            anchor="w", padx=16, pady=(12, 0))
        self.logbox = ctk.CTkTextbox(lc_, font=app.f_small, fg_color="transparent",
                                     state="disabled", wrap="word")
        self.logbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        tc = card(right)
        tc.grid(row=2, column=0, sticky="ew")
        row = ctk.CTkFrame(tc, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(16, 8))
        row.grid_columnconfigure(1, weight=1)
        self.reg(ctk.CTkLabel(row, text="", font=app.f_body), "epochs").grid(
            row=0, column=0, padx=(0, 10))
        self.epochs = ctk.CTkOptionMenu(row, values=["30", "50", "80"],
                                        width=90, fg_color=C["field"],
                                        text_color=C["text"],
                                        button_color=self.accent)
        self.epochs.set("50")
        self.epochs.grid(row=0, column=1, sticky="w")
        self.btn_train = ctk.CTkButton(row, height=48, corner_radius=14,
                                       font=app.f_btn, fg_color=self.accent,
                                       hover_color="#25A85A", command=self.train)
        self.btn_train.grid(row=0, column=2, sticky="e")
        self.prog = ctk.CTkProgressBar(tc, height=10, progress_color=self.accent)
        self.prog.set(0)
        self.prog.pack(fill="x", padx=18, pady=(0, 8))
        self.model_lbl = ctk.CTkLabel(tc, text="", font=app.f_small,
                                      text_color=C["sub"])
        self.model_lbl.pack(anchor="w", padx=18, pady=(0, 14))
        self.retext()

    def retext(self):
        super().retext()
        self.btn_rec.configure(text=self.app.t("rec"))
        self.btn_train.configure(text=self.app.t("train"))
        self.refresh()

    def on_show(self):
        self.refresh()

    def on_lang(self):
        self.refresh()

    def lang_dir(self):
        import os
        return os.path.join(lc.DATA_DIR, self.app.lang)

    def refresh(self):
        import os
        counts, root = {}, self.lang_dir()
        if os.path.isdir(root):
            for w in os.listdir(root):
                p = os.path.join(root, w)
                if os.path.isdir(p):
                    counts[w] = len([f for f in os.listdir(p)
                                     if f.endswith(".npy")])
        words = list(dict.fromkeys(S.SUGGEST[self.app.lang] + sorted(counts)))
        cur = self.word.get()
        self.word.configure(values=words)
        self.word.set(cur if cur in words or cur else words[0])
        self.counts.configure(state="normal")
        self.counts.delete("1.0", "end")
        for w in words:
            self.counts.insert("end", f"{w}  ·  {counts.get(w, 0)}\n")
        self.counts.configure(state="disabled")
        ok = self.app.lip.model is not None
        self.model_lbl.configure(
            text=("✔ " + self.app.t("model_ready")) if ok
            else ("○ " + self.app.t("model_none")),
            text_color=C["ok"] if ok else C["sub"])

    # --- rekam ---
    def start_rec(self):
        w = self.word.get().strip().lower()
        if not w:
            self.status.configure(text=self.app.t("need_word"))
            return
        if self.rec or self.training:
            return
        self.rec = {"word": w, "t0": time.time(), "frames": [], "phase": "count"}
        self.btn_rec.configure(state="disabled")

    def handle_rec(self, roi):
        import os
        import numpy as np
        r = self.rec
        if r["phase"] == "count":
            left = 3 - int(time.time() - r["t0"])
            if left > 0:
                self.big.configure(text=str(left), text_color=C["bad"])
                return
            r["phase"] = "rec"
        self.big.configure(text="REC ●", text_color=C["bad"])
        r["frames"].append(roi)
        if len(r["frames"]) >= lc.SEQ_LEN:
            d = os.path.join(self.lang_dir(), r["word"])
            os.makedirs(d, exist_ok=True)
            np.save(os.path.join(d, f"{int(time.time() * 1000)}.npy"),
                    np.stack(r["frames"]))
            self.status.configure(text=f"{self.app.t('saved')}: {r['word']}")
            self.rec = None
            self.btn_rec.configure(state="normal")
            self.big.configure(text="…", text_color=C["text"])
            self.refresh()

    def on_frame(self, frame, roi, lm):
        if roi is not None and self.rec:
            self.handle_rec(roi)
        self.cam.show(frame)

    # --- latih ---
    def train(self):
        if self.training or self.rec:
            return
        self.training = True
        self.btn_train.configure(state="disabled")
        self.prog.configure(mode="indeterminate")
        self.prog.start()
        lang, ep = self.app.lang, int(self.epochs.get())
        q = self.app.ui_q

        def work():
            try:
                import train
                msg = train.train(lang, epochs=ep,
                                  log=lambda s: q.put(("train_log", s)))
            except Exception as e:  # noqa
                msg = f"Error: {e}"
            q.put(("train_done", msg))

        threading.Thread(target=work, daemon=True).start()

    def append_log(self, s):
        self.logbox.configure(state="normal")
        self.logbox.insert("end", s + "\n")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")

    def on_event(self, kind, p):
        if kind == "train_log":
            self.append_log(p)
        elif kind == "train_done":
            self.training = False
            self.append_log(p)
            self.prog.stop()
            self.prog.configure(mode="determinate")
            self.prog.set(1 if not p.startswith("Error") else 0)
            self.btn_train.configure(state="normal")
            self.app.lip.load(self.app.lang)
            self.refresh()


# ============================ APLIKASI ============================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("SenseBridge")
        self.geometry("1320x820")
        self.minsize(1180, 740)
        self.configure(fg_color=C["bg"])
        self.lang = "id"
        self.ui_q = queue.Queue()
        self.thr = tk.DoubleVar(value=0.70)

        self.f_title = ctk.CTkFont(size=28, weight="bold")
        self.f_sub = ctk.CTkFont(size=14)
        self.f_body = ctk.CTkFont(size=16)
        self.f_btn = ctk.CTkFont(size=16, weight="bold")
        self.f_small = ctk.CTkFont(size=12)
        self.f_huge = ctk.CTkFont(size=40, weight="bold")
        self.f_caption = ctk.CTkFont(size=40, weight="bold")
        self.f_caption_m = ctk.CTkFont(size=26)

        self.speaker = services.Speaker()
        emit = lambda k, p: self.ui_q.put((k, p))        # noqa: E731
        self.listener = services.SpeechListener(emit, lambda: self.lang)
        self.detector = services.ObstacleDetector()
        self.lip = services.LipEngine()
        self.lip.load(self.lang)

        self.cap = cv2.VideoCapture(0)
        self._cam_retry = time.time()
        self.fm = lc.mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True,
                                      min_detection_confidence=0.5,
                                      min_tracking_confidence=0.5)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._sidebar()
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=22, pady=18)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.pages = {"netra": BlindPage(self, self.content),
                      "rungu": DeafPage(self, self.content),
                      "wicara": MutePage(self, self.content),
                      "latih": TrainPage(self, self.content)}
        for p in self.pages.values():
            p.grid(row=0, column=0, sticky="nsew")
        self.current = None
        self.show("netra")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(20, self.loop)

    def t(self, key):
        return S.TXT[self.lang].get(key) or S.TXT["id"].get(key, key)

    # ---------- sidebar ----------
    def _sidebar(self):
        sb = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=C["side"])
        sb.grid(row=0, column=0, sticky="ns")
        sb.grid_propagate(False)
        ctk.CTkLabel(sb, text="SenseBridge", font=ctk.CTkFont(size=26, weight="bold")
                     ).pack(anchor="w", padx=22, pady=(26, 0))
        self.app_sub = ctk.CTkLabel(sb, text="", font=self.f_small,
                                    text_color=C["sub"])
        self.app_sub.pack(anchor="w", padx=22, pady=(0, 22))

        self.nav = {}
        for key, icon in (("netra", "👁"), ("rungu", "👂"),
                          ("wicara", "🗣"), ("latih", "🧠")):
            if key == "latih":
                ctk.CTkFrame(sb, height=1, fg_color=C["idle"]).pack(
                    fill="x", padx=22, pady=14)
            b = ctk.CTkButton(sb, text="", anchor="w", height=50,
                              corner_radius=14, font=self.f_btn,
                              fg_color="transparent", text_color=C["text"],
                              hover_color=C["idle"],
                              command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=14, pady=3)
            self.nav[key] = (b, icon)

        bottom = ctk.CTkFrame(sb, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=18, pady=20)
        self.lang_lbl = ctk.CTkLabel(bottom, text="", font=self.f_small,
                                     text_color=C["sub"])
        self.lang_lbl.pack(anchor="w")
        self.seg = ctk.CTkSegmentedButton(bottom, values=["Indonesia", "English"],
                                          command=self.on_lang_pick, height=36)
        self.seg.set("Indonesia")
        self.seg.pack(fill="x", pady=(4, 14))
        self.big_var = tk.BooleanVar(value=False)
        self.dark_var = tk.BooleanVar(value=True)
        self.sw_big = ctk.CTkSwitch(bottom, text="", variable=self.big_var,
                                    onvalue=True, offvalue=False,
                                    command=self.on_big, font=self.f_small)
        self.sw_big.pack(anchor="w", pady=4)
        self.sw_dark = ctk.CTkSwitch(bottom, text="", variable=self.dark_var,
                                     onvalue=True, offvalue=False,
                                     command=self.on_dark, font=self.f_small)
        self.sw_dark.pack(anchor="w", pady=4)
        self.retext_sidebar()

    def retext_sidebar(self):
        self.app_sub.configure(text=self.t("app_sub"))
        self.lang_lbl.configure(text=self.t("lang_label"))
        self.sw_big.configure(text=self.t("big_text"))
        self.sw_dark.configure(text=self.t("dark_mode"))
        for key, (b, icon) in self.nav.items():
            b.configure(text=f"{icon}   {self.t('nav_' + key)}")

    def on_lang_pick(self, value):
        self.lang = "id" if value == "Indonesia" else "en"
        self.lip.load(self.lang)
        self.retext_sidebar()
        for p in self.pages.values():
            p.retext()
            p.on_lang()

    def on_big(self):
        big = self.big_var.get()
        self.f_caption.configure(size=64 if big else 40)
        self.f_caption_m.configure(size=36 if big else 26)
        self.f_body.configure(size=20 if big else 16)

    def on_dark(self):
        ctk.set_appearance_mode("dark" if self.dark_var.get() else "light")

    def show(self, name):
        if self.current:
            self.current.on_hide()
        self.current = self.pages[name]
        self.current.tkraise()
        self.current.on_show()
        for k, (b, _) in self.nav.items():
            b.configure(fg_color=self.pages[k].accent if k == name
                        else "transparent",
                        text_color="white" if k == name else C["text"])

    # ---------- loop kamera ----------
    def loop(self):
        ok, frame = self.cap.read()
        if ok:
            frame = cv2.flip(frame, 1)
            roi, lm = None, None
            if self.current.needs_face:
                res = self.fm.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if res.multi_face_landmarks:
                    lm = res.multi_face_landmarks[0].landmark
                    roi, (x1, y1, x2, y2) = lc.get_mouth_roi(frame, lm)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (88, 199, 52), 2)
            self.current.on_frame(frame, roi, lm)
        elif not self.cap.isOpened() and time.time() - self._cam_retry > 3:
            # kamera belum terbuka (di macOS: izin kamera baru saja diberikan,
            # atau kamera sedang dipakai aplikasi lain) -> coba buka ulang
            self._cam_retry = time.time()
            self.cap.release()
            self.cap = cv2.VideoCapture(0)
        try:
            while True:
                kind, payload = self.ui_q.get_nowait()
                for p in self.pages.values():
                    p.on_event(kind, payload)
        except queue.Empty:
            pass
        self.after(15, self.loop)

    def on_close(self):
        self.listener.stop()
        self.cap.release()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()