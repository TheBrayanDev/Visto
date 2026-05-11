import subprocess
import threading
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
from sqlmodel import Session
from database import init_db, get_session
from models import ScanHistory
from ml_services import load_models, detect_objects_np, translate_text

yolo = None
tokenizer = None
model = None

NLLB_LANG_TO_VOICE = {
    "spa_Latn": "es",
    "fra_Latn": "fr",
    "deu_Latn": "de",
    "jpn_Jpan": "ja",
}

LANGS = [
    ("Spanish", "spa_Latn"),
    ("French", "fra_Latn"),
    ("German", "deu_Latn"),
    ("Japanese", "jpn_Jpan"),
    ("Chinese", "zho_Hans"),
]


def speak(text: str, target_lang: str = "eng_Latn"):
    lang_code = NLLB_LANG_TO_VOICE.get(target_lang)
    if not lang_code:
        return
    def _speak():
        try:
            subprocess.run(["spd-say", "-l", lang_code, text], capture_output=True, timeout=10)
        except Exception:
            pass
    threading.Thread(target=_speak, daemon=True).start()


class VistoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Visto")
        self.root.configure(bg="#0f0f13")
        self.root.minsize(500, 400)
        self.geometry = (800, 700)

        self.cap = cv2.VideoCapture(0)
        self.current_frame = None
        self.translating = False

        self.main_frame = tk.Frame(self.root, bg="#0f0f13")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        self.build_ui()
        self.update_webcam()

    def build_ui(self):
        header = tk.Frame(self.main_frame, bg="#0f0f13")
        header.pack(pady=(0, 12))
        tk.Label(header, text="Visto", font=("Helvetica", 36, "bold"),
                 fg="#a855f7", bg="#0f0f13").pack()
        tk.Label(header, text="Detect  ·  Translate  ·  Speak",
                 font=("Helvetica", 11), fg="#888", bg="#0f0f13").pack()

        self.video_label = tk.Label(self.main_frame, bg="#000", bd=0, highlightthickness=0)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        controls = tk.Frame(self.main_frame, bg="#0f0f13")
        controls.pack(pady=(8, 4))

        self.lang_var = tk.StringVar()
        self.lang_menu = ttk.Combobox(controls, textvariable=self.lang_var, state="readonly", width=18, font=("Helvetica", 11))
        self.lang_menu["values"] = [f"{name}" for name, code in LANGS]
        self.lang_menu.current(0)
        self.lang_menu.pack(side=tk.LEFT, padx=(0, 8))

        self.translate_btn = tk.Button(controls, text="Translate", command=self.on_translate,
                                       font=("Helvetica", 11, "bold"), bg="#6366f1", fg="#fff",
                                       activebackground="#a855f7", activeforeground="#fff",
                                       padx=20, pady=4, bd=0, cursor="hand2")
        self.translate_btn.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.main_frame, textvariable=self.status_var, font=("Helvetica", 9),
                               fg="#888", bg="#0f0f13", anchor="w")
        status_bar.pack(fill=tk.X, pady=(0, 4))

        self.result_frame = tk.Frame(self.main_frame, bg="#1a1a24", bd=1, relief=tk.FLAT)
        self.result_frame.pack(fill=tk.BOTH, pady=(4, 0))
        self.result_inner = tk.Frame(self.result_frame, bg="#1a1a24")
        self.result_inner.pack(padx=12, pady=8, fill=tk.BOTH)

        tk.Label(self.result_inner, text="DETECTIONS", font=("Helvetica", 8, "bold"),
                 fg="#888", bg="#1a1a24").pack(anchor="w")

        self.items_frame = tk.Frame(self.result_inner, bg="#1a1a24")
        self.items_frame.pack(fill=tk.BOTH, pady=(4, 0))

        self.no_data_label = tk.Label(self.items_frame, text="Take a snapshot to detect objects",
                                       font=("Helvetica", 10), fg="#555", bg="#1a1a24")
        self.no_data_label.pack(pady=6)

    def get_target_lang(self) -> str:
        idx = self.lang_menu.current()
        if 0 <= idx < len(LANGS):
            return LANGS[idx][1]
        return "spa_Latn"

    def update_webcam(self):
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            h, w = frame.shape[:2]
            vw = self.video_label.winfo_width()
            vh = self.video_label.winfo_height()
            if vw > 10 and vh > 10:
                scale = min(vh / h, vw / w)
                new_w, new_h = int(w * scale), int(h * scale)
                display = cv2.resize(frame, (new_w, new_h))
                display = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(display)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
        self.root.after(30, self.update_webcam)

    def on_translate(self):
        if self.translating or self.current_frame is None:
            return
        self.translating = True
        self.translate_btn.configure(state=tk.DISABLED, text="Translating...")
        self.status_var.set("Detecting and translating...")
        threading.Thread(target=self.do_translate, daemon=True).start()

    def do_translate(self):
        try:
            frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            target_lang = self.get_target_lang()

            detections = detect_objects_np(yolo, frame_rgb)
            detections.sort(key=lambda d: d["confidence"], reverse=True)
            top5 = detections[:5]

            for d in top5:
                d["translation"] = translate_text(tokenizer, model, d["label"], target_lang)

            if top5:
                top = top5[0]
                session = next(get_session())
                record = ScanHistory(
                    english_label=top["label"],
                    translated_label=top["translation"],
                    target_language=target_lang,
                    confidence=top["confidence"],
                )
                session.add(record)
                session.commit()
                session.close()

                speak(top["translation"], target_lang)

            self.root.after(0, self.show_results, top5)
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {e}"))
        finally:
            self.root.after(0, self.reset_button)

    def show_results(self, detections):
        for w in self.items_frame.winfo_children():
            w.destroy()

        if not detections:
            self.no_data_label = tk.Label(self.items_frame, text="No objects detected. Try a different angle.",
                                           font=("Helvetica", 10), fg="#f87171", bg="#1a1a24")
            self.no_data_label.pack(pady=6)
            self.status_var.set("No objects detected")
            return

        for i, d in enumerate(detections):
            row = tk.Frame(self.items_frame, bg="#1a1a24")
            row.pack(fill=tk.X, pady=2)

            rank = tk.Label(row, text=str(i + 1), font=("Helvetica", 9, "bold"),
                            width=2, height=1, bg="#333", fg="#fff")
            rank.pack(side=tk.LEFT, padx=(0, 6))

            tk.Label(row, text=d["label"], font=("Helvetica", 10), fg="#aaa", bg="#1a1a24").pack(side=tk.LEFT, padx=(0, 4))
            tk.Label(row, text="→", font=("Helvetica", 10, "bold"), fg="#6366f1", bg="#1a1a24").pack(side=tk.LEFT, padx=(0, 4))
            tk.Label(row, text=d["translation"], font=("Helvetica", 10, "bold"), fg="#e8e8ed", bg="#1a1a24").pack(side=tk.LEFT, padx=(0, 4))

            conf_pct = f"{d['confidence'] * 100:.1f}%"
            tk.Label(row, text=conf_pct, font=("Helvetica", 9, "bold"), fg="#4ade80", bg="#1a1a24").pack(side=tk.RIGHT)

        self.status_var.set(f"Detected {len(detections)} objects")

    def reset_button(self):
        self.translating = False
        self.translate_btn.configure(state=tk.NORMAL, text="Translate")

    def destroy(self):
        self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    import sys

    print("Initializing database...")
    init_db()

    print("Loading models (YOLOv8, NLLB-200)...")
    yolo, tokenizer, model = load_models()
    print("Models loaded.")

    root = tk.Tk()
    app = VistoApp(root)
    try:
        root.mainloop()
    finally:
        app.destroy()
