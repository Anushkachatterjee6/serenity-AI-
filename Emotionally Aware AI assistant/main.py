"""
main.py
--------
Entry point for Aura — Emotion-Aware Mental Health AI Assistant.
Wires together all modules:
  EmotionDetector → MemoryEngine → ResponseGenerator → GUI

Voice input (optional): uses SpeechRecognition + pyttsx3
"""

import threading
import queue
import time
import os
from tkinter import messagebox

# ── Local modules ──────────────────────────────────────────────────────────
from emotion_detector import EmotionDetector
from memory_engine import MemoryEngine
from response_generator import ResponseGenerator
from gui import AuraGUI


# ── Optional: voice libraries ──────────────────────────────────────────────
try:
    import speech_recognition as sr      # type: ignore
    VOICE_INPUT_AVAILABLE = True
except ImportError:
    VOICE_INPUT_AVAILABLE = False

try:
    import pyttsx3                        # type: ignore
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


# ===========================================================================
# Application Controller
# ===========================================================================

class AuraApp:
    """
    Orchestrates all modules and manages threading so the GUI stays responsive.
    """

    def __init__(self):
        # ── Initialise core modules ─────────────────────────────────────
        print("[Aura] Initialising EmotionDetector …")
        self.emotion_detector = EmotionDetector(use_transformer=False)

        print("[Aura] Initialising MemoryEngine …")
        self.memory = MemoryEngine(log_dir="logs")

        print("[Aura] Initialising ResponseGenerator …")
        self.response_gen = ResponseGenerator(self.memory, use_api=True)

        # ── Voice components ────────────────────────────────────────────
        self.recognizer = sr.Recognizer() if VOICE_INPUT_AVAILABLE else None
        self.tts_engine = None
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 165)
                self.tts_engine.setProperty("volume", 0.9)
            except Exception as e:
                print(f"[Aura] TTS init failed: {e}")
                self.tts_engine = None

        # ── Worker queue for background processing ──────────────────────
        self._response_queue: queue.Queue = queue.Queue()

        # ── Build GUI ───────────────────────────────────────────────────
        print("[Aura] Building GUI …")
        self.gui = AuraGUI(
            on_send=self._on_user_send,
            on_voice=self._on_voice_input if VOICE_INPUT_AVAILABLE else None,
            on_save=self._on_save_session,
            on_reset=self._on_reset_session,
        )

        # Poll the response queue every 100 ms
        self.gui.root.after(100, self._poll_response_queue)

        print("[Aura] Ready.")

    # -----------------------------------------------------------------------
    # User sends a message
    # -----------------------------------------------------------------------

    def _on_user_send(self, text: str):
        """Called by GUI when the user submits a message."""
        if not text.strip():
            return

        # Render user message immediately
        self.gui.add_user_message(text)
        self.gui.set_input_enabled(False)
        self.gui.show_typing()

        # Run emotion detection + response generation in background thread
        threading.Thread(
            target=self._process_message,
            args=(text,),
            daemon=True
        ).start()

    def _process_message(self, text: str):
        """Background thread: detect emotion, generate response, queue result."""
        try:
            # 1. Detect emotion
            emotion, confidence = self.emotion_detector.detect(text)

            # 2. Update memory with user turn
            self.memory.add_user_message(text, emotion, confidence)

            # 3. Simulate thinking delay for UX
            time.sleep(0.8)

            # 4. Generate response
            response = self.response_gen.generate(text, emotion, confidence)

            # 5. Update memory with AI response
            self.memory.add_assistant_message(response)

            # 6. Queue result back to GUI thread
            self._response_queue.put({
                "type": "response",
                "emotion": emotion,
                "confidence": confidence,
                "response": response,
            })

        except Exception as e:
            print(f"[Aura] Error processing message: {e}")
            self._response_queue.put({
                "type": "error",
                "message": "I'm sorry, something went wrong. Please try again.",
            })

    # -----------------------------------------------------------------------
    # Poll queue → update GUI (must run on main thread)
    # -----------------------------------------------------------------------

    def _poll_response_queue(self):
        """Check for completed responses and update the GUI."""
        try:
            while True:
                item = self._response_queue.get_nowait()

                if item["type"] == "response":
                    self.gui.hide_typing()
                    self.gui.update_emotion(item["emotion"], item["confidence"])
                    self.gui.add_ai_message(item["response"])
                    self.gui.set_input_enabled(True)

                    # Optional TTS
                    if self.tts_engine:
                        threading.Thread(
                            target=self._speak,
                            args=(item["response"],),
                            daemon=True
                        ).start()

                elif item["type"] == "voice_text":
                    self.gui.set_voice_active(False)
                    self.gui.set_input_text(item["text"])
                    self.gui.add_system_message(f"🎤 Heard: \"{item['text']}\"")

                elif item["type"] == "voice_error":
                    self.gui.set_voice_active(False)
                    self.gui.add_system_message(f"🎤 {item['message']}")

                elif item["type"] == "error":
                    self.gui.hide_typing()
                    self.gui.add_ai_message(item["message"])
                    self.gui.set_input_enabled(True)

                elif item["type"] == "session_saved":
                    self.gui.add_system_message(f"💾 Session saved to: {item['path']}")

        except queue.Empty:
            pass

        # Reschedule
        self.gui.root.after(100, self._poll_response_queue)

    # -----------------------------------------------------------------------
    # Voice input
    # -----------------------------------------------------------------------

    def _on_voice_input(self):
        """Called by GUI microphone button."""
        if not VOICE_INPUT_AVAILABLE:
            return
        self.gui.set_voice_active(True)
        self.gui.add_system_message("🎤 Listening… speak now.")
        threading.Thread(target=self._listen_voice, daemon=True).start()

    def _listen_voice(self):
        """Background thread: capture microphone input."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)

            text = self.recognizer.recognize_google(audio)
            self._response_queue.put({"type": "voice_text", "text": text})

        except sr.WaitTimeoutError:
            self._response_queue.put({"type": "voice_error",
                                      "message": "No speech detected. Try again."})
        except sr.UnknownValueError:
            self._response_queue.put({"type": "voice_error",
                                      "message": "Couldn't understand the audio. Please try again."})
        except sr.RequestError as e:
            self._response_queue.put({"type": "voice_error",
                                      "message": f"Speech service error: {e}"})
        except Exception as e:
            self._response_queue.put({"type": "voice_error",
                                      "message": f"Voice input failed: {e}"})

    # -----------------------------------------------------------------------
    # TTS output
    # -----------------------------------------------------------------------

    def _speak(self, text: str):
        """Background thread: text-to-speech output."""
        try:
            if self.tts_engine:
                # Strip emoji-like characters that TTS can't pronounce
                import re
                clean = re.sub(r"[^\x00-\x7F]+", "", text)
                self.tts_engine.say(clean)
                self.tts_engine.runAndWait()
        except Exception as e:
            print(f"[Aura] TTS error: {e}")

    # -----------------------------------------------------------------------
    # Session management
    # -----------------------------------------------------------------------

    def _on_save_session(self):
        """Save session to file."""
        def _save():
            path = self.memory.save_session()
            self._response_queue.put({"type": "session_saved", "path": path})
        threading.Thread(target=_save, daemon=True).start()

    def _on_reset_session(self):
        """Reset conversation for a new session."""
        # Save current session first
        self.memory.save_session()
        self.memory.reset()

        # Clear chat window
        for widget in self.gui.chat_frame.winfo_children():
            widget.destroy()

        # Reset emotion badge
        self.gui.update_emotion("neutral", 0.5)

        # Show welcome again
        self.gui._show_welcome()
        self.gui.add_system_message("✨ New session started.")

    # -----------------------------------------------------------------------
    # Run
    # -----------------------------------------------------------------------

    def run(self):
        self.gui.run()


# ===========================================================================
# Entry point
# ===========================================================================

def main():
    print("=" * 55)
    print("  ✦  Aura — Emotion-Aware Mental Health AI Assistant")
    print("=" * 55)

    # Check for logs directory
    os.makedirs("logs", exist_ok=True)

    app = AuraApp()
    app.run()


if __name__ == "__main__":
    main()
