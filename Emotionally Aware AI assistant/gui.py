"""
gui.py
-------
Tkinter GUI for the Emotion-Aware Mental Health AI Assistant "Aura".
Clean, calming design with a scrollable chat window, emotion badge,
voice input button, and settings panel.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font as tkfont
import threading
import queue
import time
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Color palette — soft, therapeutic aesthetic
# ---------------------------------------------------------------------------
COLORS = {
    "bg":           "#1a1a2e",   # deep navy background
    "sidebar":      "#16213e",   # slightly lighter navy
    "card":         "#0f3460",   # card / header
    "accent":       "#e94560",   # rose accent
    "accent2":      "#533483",   # purple accent
    "user_bubble":  "#0f3460",   # user message bubble
    "ai_bubble":    "#1a1a3e",   # AI message bubble
    "text_main":    "#eaeaea",   # main text
    "text_muted":   "#8892b0",   # muted text
    "input_bg":     "#0f3460",   # input field background
    "btn":          "#e94560",   # button
    "btn_hover":    "#c73652",   # button hover
    "online":       "#64ffda",   # online indicator
    "emotion_bg": {
        "happy":    "#2d5a27",
        "sad":      "#1a3a5c",
        "anxious":  "#5a3a1a",
        "angry":    "#5a1a1a",
        "lonely":   "#2d1a5c",
        "insecure": "#3a2d1a",
        "neutral":  "#1e2d3d",
        "crisis":   "#5a0000",
    },
    "emotion_text": {
        "happy":    "#7fff6f",
        "sad":      "#6fb3ff",
        "anxious":  "#ffb36f",
        "angry":    "#ff6f6f",
        "lonely":   "#b36fff",
        "insecure": "#ffd76f",
        "neutral":  "#8892b0",
        "crisis":   "#ff4444",
    },
}

EMOTION_EMOJI = {
    "happy": "😊",
    "sad": "😔",
    "anxious": "😰",
    "angry": "😠",
    "lonely": "🥺",
    "insecure": "😟",
    "neutral": "😐",
    "crisis": "🆘",
}


# ---------------------------------------------------------------------------
# Main GUI class
# ---------------------------------------------------------------------------

class AuraGUI:
    """
    Main application window for Aura — Mental Health AI Assistant.
    """

    def __init__(self,
                 on_send: Callable[[str], None],
                 on_voice: Optional[Callable[[], None]] = None,
                 on_save: Optional[Callable[[], None]] = None,
                 on_reset: Optional[Callable[[], None]] = None):
        """
        Parameters
        ----------
        on_send  : callback(user_text) — called when user sends a message
        on_voice : callback() — called when microphone button is pressed
        on_save  : callback() — called when save session is pressed
        on_reset : callback() — called when new session is pressed
        """
        self.on_send = on_send
        self.on_voice = on_voice
        self.on_save = on_save
        self.on_reset = on_reset

        self.root = tk.Tk()
        self._setup_window()
        self._load_fonts()
        self._build_layout()
        self._bind_shortcuts()

        self._voice_active = False
        self._typing_after_id = None

    # ------------------------------------------------------------------
    # Window & fonts
    # ------------------------------------------------------------------

    def _setup_window(self):
        self.root.title("Aura — Mental Health Companion")
        self.root.geometry("860x680")
        self.root.minsize(700, 500)
        self.root.configure(bg=COLORS["bg"])
        # Centre on screen
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _load_fonts(self):
        self.font_title  = ("Georgia", 18, "bold")
        self.font_sub    = ("Helvetica", 10)
        self.font_body   = ("Helvetica", 12)
        self.font_small  = ("Helvetica", 9)
        self.font_input  = ("Helvetica", 13)
        self.font_emoji  = ("Segoe UI Emoji", 14) if tk.TkVersion >= 8.6 else ("Helvetica", 14)

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_layout(self):
        # ── Top header bar ──────────────────────────────────────────────
        self.header = tk.Frame(self.root, bg=COLORS["card"], height=62)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        # Logo / title
        tk.Label(self.header, text="✦  Aura", font=("Georgia", 17, "bold"),
                 bg=COLORS["card"], fg=COLORS["text_main"]).pack(side="left", padx=18, pady=10)
        tk.Label(self.header, text="Mental Health Companion",
                 font=("Helvetica", 9), bg=COLORS["card"],
                 fg=COLORS["text_muted"]).pack(side="left", padx=0, pady=10)

        # Online indicator
        online_frame = tk.Frame(self.header, bg=COLORS["card"])
        online_frame.pack(side="right", padx=18)
        tk.Canvas(online_frame, width=10, height=10, bg=COLORS["card"],
                  highlightthickness=0).pack(side="left")
        self.status_dot = tk.Canvas(online_frame, width=10, height=10,
                                    bg=COLORS["card"], highlightthickness=0)
        self.status_dot.pack(side="left")
        self.status_dot.create_oval(1, 1, 9, 9, fill=COLORS["online"], outline="")
        tk.Label(online_frame, text="Online", font=self.font_small,
                 bg=COLORS["card"], fg=COLORS["online"]).pack(side="left", padx=4)

        # Action buttons in header
        btn_style = dict(bg=COLORS["card"], fg=COLORS["text_muted"],
                         font=self.font_small, relief="flat",
                         cursor="hand2", bd=0, padx=8, pady=4)
        if self.on_save:
            tk.Button(self.header, text="💾 Save", command=self._handle_save,
                      **btn_style).pack(side="right", padx=4)
        if self.on_reset:
            tk.Button(self.header, text="🔄 New Session", command=self._handle_reset,
                      **btn_style).pack(side="right", padx=4)

        # ── Emotion badge bar ────────────────────────────────────────────
        self.emotion_bar = tk.Frame(self.root, bg=COLORS["sidebar"], height=36)
        self.emotion_bar.pack(fill="x", side="top")
        self.emotion_bar.pack_propagate(False)

        tk.Label(self.emotion_bar, text="Detected Emotion:",
                 font=self.font_small, bg=COLORS["sidebar"],
                 fg=COLORS["text_muted"]).pack(side="left", padx=14, pady=8)

        self.emotion_badge = tk.Label(self.emotion_bar, text="  😐  neutral  ",
                                      font=("Helvetica", 9, "bold"),
                                      bg=COLORS["emotion_bg"]["neutral"],
                                      fg=COLORS["emotion_text"]["neutral"],
                                      padx=8, pady=2)
        self.emotion_badge.pack(side="left", pady=6)

        self.confidence_label = tk.Label(self.emotion_bar, text="",
                                         font=self.font_small,
                                         bg=COLORS["sidebar"],
                                         fg=COLORS["text_muted"])
        self.confidence_label.pack(side="left", padx=10)

        # Typing indicator (right side)
        self.typing_label = tk.Label(self.emotion_bar, text="",
                                     font=self.font_small,
                                     bg=COLORS["sidebar"],
                                     fg=COLORS["accent"])
        self.typing_label.pack(side="right", padx=16)

        # ── Chat canvas (scrollable) ─────────────────────────────────────
        chat_container = tk.Frame(self.root, bg=COLORS["bg"])
        chat_container.pack(fill="both", expand=True, padx=12, pady=(10, 0))

        self.canvas = tk.Canvas(chat_container, bg=COLORS["bg"],
                                highlightthickness=0)
        scrollbar = ttk.Scrollbar(chat_container, orient="vertical",
                                  command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.chat_frame = tk.Frame(self.canvas, bg=COLORS["bg"])
        self.chat_window = self.canvas.create_window(
            (0, 0), window=self.chat_frame, anchor="nw"
        )

        self.chat_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse scroll
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        # Welcome message
        self._show_welcome()

        # ── Input area ───────────────────────────────────────────────────
        input_frame = tk.Frame(self.root, bg=COLORS["sidebar"], pady=12)
        input_frame.pack(fill="x", side="bottom")

        inner = tk.Frame(input_frame, bg=COLORS["sidebar"])
        inner.pack(fill="x", padx=14)

        # Text input
        self.input_var = tk.StringVar()
        self.input_box = tk.Text(inner, height=3, font=self.font_input,
                                 bg=COLORS["input_bg"], fg=COLORS["text_main"],
                                 insertbackground=COLORS["accent"],
                                 relief="flat", padx=12, pady=8,
                                 wrap="word")
        self.input_box.pack(side="left", fill="x", expand=True)
        self.input_box.bind("<Return>", self._on_enter_key)
        self.input_box.bind("<Shift-Return>", lambda e: None)  # allow newline

        # Placeholder
        self._set_placeholder()

        # Buttons
        btn_frame = tk.Frame(inner, bg=COLORS["sidebar"])
        btn_frame.pack(side="right", padx=(8, 0))

        # Mic button
        self.mic_btn = tk.Button(btn_frame, text="🎤",
                                 font=("Segoe UI Emoji", 16),
                                 bg=COLORS["card"], fg=COLORS["text_main"],
                                 relief="flat", cursor="hand2",
                                 width=3, height=1,
                                 command=self._handle_voice)
        self.mic_btn.pack(pady=(0, 6))

        # Send button
        self.send_btn = tk.Button(btn_frame, text="Send ➤",
                                  font=("Helvetica", 11, "bold"),
                                  bg=COLORS["btn"], fg="white",
                                  relief="flat", cursor="hand2",
                                  padx=14, pady=6,
                                  command=self._handle_send)
        self.send_btn.pack()
        self._bind_hover(self.send_btn, COLORS["btn_hover"], COLORS["btn"])

        # Hint label
        tk.Label(input_frame, text="Press Enter to send  •  Shift+Enter for new line",
                 font=("Helvetica", 8), bg=COLORS["sidebar"],
                 fg=COLORS["text_muted"]).pack(pady=(4, 0))

    # ------------------------------------------------------------------
    # Welcome message
    # ------------------------------------------------------------------

    def _show_welcome(self):
        welcome = (
            "Hello 💙 I'm Aura, your mental health companion.\n\n"
            "This is a safe, judgment-free space. You can share anything "
            "that's on your mind — feelings, worries, or just how your day went.\n\n"
            "I'm here to listen and support you. How are you feeling today?"
        )
        self.add_ai_message(welcome, animate=False)

    # ------------------------------------------------------------------
    # Chat bubble rendering
    # ------------------------------------------------------------------

    def add_user_message(self, text: str):
        """Render a user message bubble."""
        wrapper = tk.Frame(self.chat_frame, bg=COLORS["bg"])
        wrapper.pack(fill="x", padx=16, pady=4, anchor="e")

        # Spacer to push bubble right
        tk.Frame(wrapper, bg=COLORS["bg"], width=120).pack(side="left")

        bubble = tk.Frame(wrapper, bg=COLORS["user_bubble"],
                          padx=14, pady=10)
        bubble.pack(side="right", anchor="e")

        tk.Label(bubble, text="You", font=("Helvetica", 8, "bold"),
                 bg=COLORS["user_bubble"],
                 fg=COLORS["accent"]).pack(anchor="e")

        lbl = tk.Label(bubble, text=text, font=self.font_body,
                       bg=COLORS["user_bubble"], fg=COLORS["text_main"],
                       wraplength=420, justify="left", anchor="w")
        lbl.pack(anchor="e")

        self._scroll_to_bottom()

    def add_ai_message(self, text: str, animate: bool = True):
        """Render an AI message bubble, optionally with typewriter animation."""
        wrapper = tk.Frame(self.chat_frame, bg=COLORS["bg"])
        wrapper.pack(fill="x", padx=16, pady=4, anchor="w")

        # Avatar
        av = tk.Label(wrapper, text="✦", font=("Georgia", 14),
                      bg=COLORS["accent2"], fg="white",
                      width=2, height=1, padx=4, pady=4)
        av.pack(side="left", anchor="n", padx=(0, 8))

        bubble = tk.Frame(wrapper, bg=COLORS["ai_bubble"], padx=14, pady=10)
        bubble.pack(side="left", anchor="w")

        tk.Label(bubble, text="Aura", font=("Helvetica", 8, "bold"),
                 bg=COLORS["ai_bubble"],
                 fg=COLORS["accent2"]).pack(anchor="w")

        lbl = tk.Label(bubble, text="", font=self.font_body,
                       bg=COLORS["ai_bubble"], fg=COLORS["text_main"],
                       wraplength=460, justify="left", anchor="w")
        lbl.pack(anchor="w")

        if animate:
            self._typewriter(lbl, text)
        else:
            lbl.config(text=text)

        self._scroll_to_bottom()

    def add_system_message(self, text: str):
        """Render a centered system / info message."""
        wrapper = tk.Frame(self.chat_frame, bg=COLORS["bg"])
        wrapper.pack(fill="x", padx=30, pady=6)
        tk.Label(wrapper, text=text, font=self.font_small,
                 bg=COLORS["bg"], fg=COLORS["text_muted"],
                 wraplength=600, justify="center").pack()
        self._scroll_to_bottom()

    # ------------------------------------------------------------------
    # Emotion badge update
    # ------------------------------------------------------------------

    def update_emotion(self, emotion: str, confidence: float):
        """Update the emotion badge in the toolbar."""
        emoji = EMOTION_EMOJI.get(emotion, "😐")
        bg = COLORS["emotion_bg"].get(emotion, COLORS["emotion_bg"]["neutral"])
        fg = COLORS["emotion_text"].get(emotion, COLORS["emotion_text"]["neutral"])

        self.emotion_badge.config(
            text=f"  {emoji}  {emotion}  ",
            bg=bg, fg=fg
        )
        pct = int(confidence * 100)
        self.confidence_label.config(text=f"({pct}% confidence)")

    # ------------------------------------------------------------------
    # Typing indicator
    # ------------------------------------------------------------------

    def show_typing(self):
        self.typing_label.config(text="Aura is typing…")
        self.root.after(100, self._animate_typing)

    def hide_typing(self):
        if self._typing_after_id:
            self.root.after_cancel(self._typing_after_id)
        self.typing_label.config(text="")

    def _animate_typing(self):
        dots = ["Aura is typing.", "Aura is typing..", "Aura is typing..."]
        current = self.typing_label.cget("text")
        idx = dots.index(current) if current in dots else 0
        self.typing_label.config(text=dots[(idx + 1) % 3])
        self._typing_after_id = self.root.after(400, self._animate_typing)

    # ------------------------------------------------------------------
    # Enable / disable input
    # ------------------------------------------------------------------

    def set_input_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.input_box.config(state=state)
        self.send_btn.config(state=state)

    # ------------------------------------------------------------------
    # Voice indicator
    # ------------------------------------------------------------------

    def set_voice_active(self, active: bool):
        self._voice_active = active
        if active:
            self.mic_btn.config(bg=COLORS["accent"], fg="white")
        else:
            self.mic_btn.config(bg=COLORS["card"], fg=COLORS["text_main"])

    def set_input_text(self, text: str):
        """Set input box text (used by voice input)."""
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", text)

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    def _handle_send(self):
        text = self.input_box.get("1.0", "end").strip()
        if not text or text == "Type your message here…":
            return
        self.input_box.delete("1.0", "end")
        self._set_placeholder()
        self.on_send(text)

    def _handle_voice(self):
        if self.on_voice:
            self.on_voice()

    def _handle_save(self):
        if self.on_save:
            self.on_save()

    def _handle_reset(self):
        if messagebox.askyesno("New Session",
                               "Start a new session? Current conversation will be saved."):
            if self.on_reset:
                self.on_reset()

    def _on_enter_key(self, event):
        if not (event.state & 0x1):   # Shift not held
            self._handle_send()
            return "break"

    # ------------------------------------------------------------------
    # Placeholder text
    # ------------------------------------------------------------------

    def _set_placeholder(self):
        if not self.input_box.get("1.0", "end").strip():
            self.input_box.insert("1.0", "Type your message here…")
            self.input_box.config(fg=COLORS["text_muted"])

    def _clear_placeholder(self, event):
        if self.input_box.get("1.0", "end").strip() == "Type your message here…":
            self.input_box.delete("1.0", "end")
            self.input_box.config(fg=COLORS["text_main"])

    # ------------------------------------------------------------------
    # Scroll helpers
    # ------------------------------------------------------------------

    def _scroll_to_bottom(self):
        self.root.after(50, lambda: self.canvas.yview_moveto(1.0))

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.chat_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ------------------------------------------------------------------
    # Typewriter animation
    # ------------------------------------------------------------------

    def _typewriter(self, label: tk.Label, text: str, index: int = 0):
        if index <= len(text):
            label.config(text=text[:index])
            self._scroll_to_bottom()
            delay = 18 if index < len(text) else 0
            self.root.after(delay, self._typewriter, label, text, index + 1)

    # ------------------------------------------------------------------
    # Hover effects
    # ------------------------------------------------------------------

    def _bind_hover(self, widget, hover_color, normal_color):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_color))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_color))

    # ------------------------------------------------------------------
    # Shortcuts
    # ------------------------------------------------------------------

    def _bind_shortcuts(self):
        self.root.bind("<Control-Return>", lambda e: self._handle_send())
        self.input_box.bind("<FocusIn>", self._clear_placeholder)
        self.input_box.bind("<FocusOut>", lambda e: self._set_placeholder())

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self):
        self.root.mainloop()

    def destroy(self):
        self.root.destroy()
