"""
memory_engine.py
-----------------
Manages conversation history, emotion trajectory, and context summaries.
This is the "brain" that gives the AI its continuity and awareness.
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import Counter


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Message:
    """A single conversation turn."""
    def __init__(self, role: str, text: str, emotion: str = "neutral", confidence: float = 0.5):
        self.role = role          # "user" | "assistant"
        self.text = text
        self.emotion = emotion
        self.confidence = confidence
        self.timestamp = datetime.now().strftime("%H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "text": self.text,
            "emotion": self.emotion,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


class MemoryEngine:
    """
    Tracks conversation history, emotion trajectory, topic threads,
    and produces contextual summaries for the response generator.
    """

    def __init__(self, max_history: int = 50, log_dir: str = "logs"):
        self.history: List[Message] = []
        self.emotion_trajectory: List[str] = []    # emotions in order
        self.max_history = max_history
        self.log_dir = log_dir
        self.session_start = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.turn_count = 0
        self.dominant_topic: Optional[str] = None   # rough topic tracker

        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def add_user_message(self, text: str, emotion: str, confidence: float):
        """Record a user turn and update emotion trajectory."""
        msg = Message("user", text, emotion, confidence)
        self.history.append(msg)
        self.emotion_trajectory.append(emotion)
        self.turn_count += 1
        self._trim_history()
        self._log_message(msg)

    def add_assistant_message(self, text: str):
        """Record an assistant turn."""
        msg = Message("assistant", text)
        self.history.append(msg)
        self._log_message(msg)

    # ------------------------------------------------------------------
    # Context & summaries
    # ------------------------------------------------------------------

    def get_recent_history(self, n_turns: int = 6) -> List[Message]:
        """Return last n_turns messages (both user + assistant)."""
        return self.history[-n_turns * 2:] if len(self.history) >= n_turns * 2 else self.history[:]

    def get_emotion_trend(self) -> Dict:
        """
        Analyse the emotion trajectory and return a summary dict:
          - dominant: most frequent emotion in recent turns
          - recent: last 3 emotions
          - improving: bool (moving towards happy/neutral)
          - worsening: bool (moving towards sad/anxious/angry)
          - stable: bool
        """
        if not self.emotion_trajectory:
            return {"dominant": "neutral", "recent": [], "improving": False,
                    "worsening": False, "stable": True}

        recent = self.emotion_trajectory[-5:]       # last 5 user emotions
        counter = Counter(recent)
        dominant = counter.most_common(1)[0][0]

        positive_set = {"happy", "neutral"}
        negative_set = {"sad", "anxious", "angry", "lonely", "insecure", "crisis"}

        # Trend: compare first half vs second half of recent window
        mid = len(recent) // 2
        first_neg = sum(1 for e in recent[:mid] if e in negative_set)
        second_neg = sum(1 for e in recent[mid:] if e in negative_set)

        improving = second_neg < first_neg
        worsening = second_neg > first_neg
        stable = not improving and not worsening

        return {
            "dominant": dominant,
            "recent": recent,
            "improving": improving,
            "worsening": worsening,
            "stable": stable,
        }

    def get_context_summary(self) -> str:
        """
        Build a short textual summary of context to feed the response generator.
        E.g.: "User has been feeling sad and lonely for 3 turns. Trend is stable."
        """
        if not self.history:
            return "This is the start of the conversation."

        trend = self.get_emotion_trend()
        dominant = trend["dominant"]
        recent = trend["recent"]
        n_user_turns = self.turn_count

        parts = []

        if n_user_turns == 1:
            parts.append("This is the first message.")
        else:
            parts.append(f"Conversation has {n_user_turns} user turns so far.")

        if recent:
            parts.append(f"Recent emotions: {', '.join(recent)}.")
            parts.append(f"Dominant emotion: {dominant}.")

        if trend["improving"]:
            parts.append("The user's mood appears to be improving.")
        elif trend["worsening"]:
            parts.append("The user's mood appears to be worsening — extra care needed.")
        else:
            parts.append("The emotional state is relatively stable.")

        # Include last user message snippet for topic continuity
        last_user = self._get_last_user_message()
        if last_user:
            snippet = last_user.text[:80].replace("\n", " ")
            parts.append(f'Last user message: "{snippet}…"' if len(last_user.text) > 80 else f'Last user message: "{last_user.text}"')

        return " ".join(parts)

    def get_repeated_emotion(self) -> Optional[str]:
        """Return emotion if user has expressed same emotion ≥ 3 consecutive turns."""
        if len(self.emotion_trajectory) < 3:
            return None
        last3 = self.emotion_trajectory[-3:]
        if len(set(last3)) == 1 and last3[0] not in ("neutral",):
            return last3[0]
        return None

    def is_first_turn(self) -> bool:
        return self.turn_count <= 1

    def get_last_emotion(self) -> str:
        return self.emotion_trajectory[-1] if self.emotion_trajectory else "neutral"

    def get_previous_emotion(self) -> str:
        return self.emotion_trajectory[-2] if len(self.emotion_trajectory) >= 2 else "neutral"

    def emotion_shifted(self) -> Optional[Tuple[str, str]]:
        """If emotion changed last turn, return (prev, current)."""
        if len(self.emotion_trajectory) >= 2:
            prev, curr = self.emotion_trajectory[-2], self.emotion_trajectory[-1]
            if prev != curr:
                return prev, curr
        return None

    # ------------------------------------------------------------------
    # Persistence / logging
    # ------------------------------------------------------------------

    def _log_message(self, msg: Message):
        """Append message to session log file."""
        log_file = os.path.join(self.log_dir, f"session_{self.session_start}.jsonl")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(msg.to_dict()) + "\n")
        except Exception as e:
            print(f"[MemoryEngine] Log error: {e}")

    def save_session(self):
        """Save entire session as a JSON file."""
        save_path = os.path.join(self.log_dir, f"full_session_{self.session_start}.json")
        data = {
            "session_start": self.session_start,
            "total_turns": self.turn_count,
            "emotion_trajectory": self.emotion_trajectory,
            "messages": [m.to_dict() for m in self.history],
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return save_path

    def reset(self):
        """Clear memory for a new session."""
        self.history.clear()
        self.emotion_trajectory.clear()
        self.turn_count = 0
        self.session_start = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _trim_history(self):
        """Keep history within max_history limit."""
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def _get_last_user_message(self) -> Optional[Message]:
        for msg in reversed(self.history):
            if msg.role == "user":
                return msg
        return None


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mem = MemoryEngine(log_dir="logs_test")
    mem.add_user_message("I feel really sad today.", "sad", 0.8)
    mem.add_assistant_message("I'm sorry to hear that. Would you like to tell me more?")
    mem.add_user_message("Nobody seems to care about me.", "lonely", 0.9)
    mem.add_assistant_message("That sounds really isolating. I'm here for you.")
    mem.add_user_message("I'm feeling a bit better after talking.", "happy", 0.6)

    print("Context summary:")
    print(mem.get_context_summary())
    print("\nEmotion trend:", mem.get_emotion_trend())
    print("Emotion shift:", mem.emotion_shifted())
