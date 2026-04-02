"""
emotion_detector.py
--------------------
Detects both explicit and implicit emotions from user text.
Uses keyword-based NLP with pattern matching as the primary engine,
with optional HuggingFace transformer model as an upgrade path.
"""

import re
from typing import Tuple, Dict, List

# ---------------------------------------------------------------------------
# Emotion lexicon  (keyword → emotion)
# ---------------------------------------------------------------------------
EMOTION_KEYWORDS: Dict[str, List[str]] = {
    "happy": [
        "happy", "joyful", "excited", "glad", "elated", "cheerful",
        "wonderful", "fantastic", "great", "amazing", "love", "blessed",
        "grateful", "thankful", "thrilled", "delighted", "pleased",
        "content", "satisfied", "awesome", "good", "fine", "well",
    ],
    "sad": [
        "sad", "unhappy", "depressed", "miserable", "heartbroken",
        "devastated", "grief", "sorrow", "cry", "crying", "tears",
        "hopeless", "worthless", "empty", "numb", "broken", "hurt",
        "pain", "suffering", "despair", "melancholy", "gloomy",
        "down", "low", "blue", "disappointed", "upset",
    ],
    "anxious": [
        "anxious", "anxiety", "worried", "nervous", "stressed", "panic",
        "fear", "scared", "terrified", "overwhelmed", "tense", "uneasy",
        "restless", "dread", "phobia", "paranoid", "jittery", "on edge",
        "can't sleep", "insomnia", "racing thoughts", "what if",
    ],
    "angry": [
        "angry", "furious", "rage", "mad", "irritated", "frustrated",
        "annoyed", "enraged", "livid", "bitter", "resentful", "hate",
        "disgusted", "outraged", "infuriated", "hostile", "aggressive",
        "fed up", "sick of", "can't stand",
    ],
    "lonely": [
        "lonely", "alone", "isolated", "abandoned", "neglected",
        "unwanted", "rejected", "left out", "excluded", "forgotten",
        "no one", "nobody", "friendless", "disconnected", "invisible",
        "unloved", "ignored", "misunderstood",
    ],
    "insecure": [
        "insecure", "jealous", "envious", "inferior", "not good enough",
        "everyone else", "better than me", "compare", "comparison",
        "ugly", "stupid", "dumb", "failure", "loser", "can't do",
        "never succeed", "always fail", "behind", "left behind",
    ],
}

# ---------------------------------------------------------------------------
# Implicit emotion patterns  (regex phrase → emotion)
# ---------------------------------------------------------------------------
IMPLICIT_PATTERNS: List[Tuple[str, str]] = [
    # Loneliness / isolation
    (r"no one (understands|cares|listens|notices)", "lonely"),
    (r"(everyone|people) (ignore|avoid|leave)s? me", "lonely"),
    (r"i (have|had) no (friends|one)", "lonely"),
    # Insecurity / comparison
    (r"(everyone|others|people) (are|seem|is) (doing|better|happier|more successful)", "insecure"),
    (r"i (can'?t|could never) (do|be|achieve|reach)", "insecure"),
    (r"why (can'?t|don'?t) i", "insecure"),
    (r"i (always|never) (mess|fail|screw)", "insecure"),
    # Sadness / hopelessness
    (r"what'?s? the (point|use)", "sad"),
    (r"nothing (matters|works|helps)", "sad"),
    (r"i (give up|can'?t go on|want to disappear)", "sad"),
    (r"(life|everything) is (pointless|meaningless|hopeless)", "sad"),
    # Anxiety
    (r"i (can'?t|don'?t know how to) (cope|handle|deal)", "anxious"),
    (r"(too much|overwhelming|too many)", "anxious"),
    (r"i keep (thinking|worrying) about", "anxious"),
    # Anger
    (r"(it'?s|this is) (so|really|extremely) (unfair|wrong)", "angry"),
    (r"why (does|do|would|did) (he|she|they|it|this)", "angry"),
    (r"i (hate|despise|can'?t stand) (this|that|him|her|them)", "angry"),
]

# ---------------------------------------------------------------------------
# Crisis keywords (used externally by the response generator)
# ---------------------------------------------------------------------------
CRISIS_KEYWORDS: List[str] = [
    "suicide", "kill myself", "end my life", "want to die", "self-harm",
    "hurt myself", "cutting", "overdose", "not worth living",
]


class EmotionDetector:
    """
    Detects explicit and implicit emotions from a text string.
    Returns the dominant emotion label and a confidence score (0-1).
    """

    def __init__(self, use_transformer: bool = False):
        self.use_transformer = use_transformer
        self._transformer_pipeline = None

        if use_transformer:
            self._load_transformer()

    # ------------------------------------------------------------------
    # Optional transformer upgrade path
    # ------------------------------------------------------------------
    def _load_transformer(self):
        """Load HuggingFace emotion classifier (requires internet + GPU RAM)."""
        try:
            from transformers import pipeline  # type: ignore
            print("[EmotionDetector] Loading transformer model …")
            self._transformer_pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None,
            )
            print("[EmotionDetector] Transformer model loaded.")
        except Exception as exc:
            print(f"[EmotionDetector] Transformer load failed ({exc}). Falling back to rule-based.")
            self._transformer_pipeline = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def detect(self, text: str) -> Tuple[str, float]:
        """
        Returns (emotion_label, confidence).
        Emotion labels: happy | sad | anxious | angry | lonely | insecure | neutral
        """
        text_lower = text.lower()

        # 1. Crisis check (highest priority)
        if any(kw in text_lower for kw in CRISIS_KEYWORDS):
            return "crisis", 1.0

        # 2. Transformer (if available)
        if self._transformer_pipeline:
            return self._transformer_detect(text)

        # 3. Rule-based hybrid
        return self._rule_based_detect(text_lower)

    def is_crisis(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in CRISIS_KEYWORDS)

    # ------------------------------------------------------------------
    # Internal engines
    # ------------------------------------------------------------------
    def _rule_based_detect(self, text_lower: str) -> Tuple[str, float]:
        scores: Dict[str, float] = {e: 0.0 for e in EMOTION_KEYWORDS}

        # --- Keyword scoring ---
        words = re.findall(r"\b\w+\b", text_lower)
        for word in words:
            for emotion, keywords in EMOTION_KEYWORDS.items():
                if word in keywords:
                    scores[emotion] += 1.0

        # --- Implicit pattern scoring ---
        for pattern, emotion in IMPLICIT_PATTERNS:
            if re.search(pattern, text_lower):
                scores[emotion] += 1.5   # implicit signals weighted higher

        # --- Negation handling (e.g. "not happy" → don't add happy) ---
        negation_re = re.compile(r"\b(not|no|never|don'?t|can'?t|won'?t)\b\s+\w+")
        for match in negation_re.finditer(text_lower):
            after = match.group().split()[-1]
            for emotion, keywords in EMOTION_KEYWORDS.items():
                if after in keywords:
                    scores[emotion] = max(0, scores[emotion] - 1.0)

        best_emotion = max(scores, key=lambda e: scores[e])
        best_score = scores[best_emotion]

        if best_score == 0:
            return "neutral", 0.5

        # Normalize confidence to 0-1 range (cap at 1.0)
        confidence = min(best_score / 5.0, 1.0)
        return best_emotion, round(confidence, 2)

    def _transformer_detect(self, text: str) -> Tuple[str, float]:
        """Use HuggingFace pipeline and map labels to our emotion set."""
        LABEL_MAP = {
            "joy": "happy", "happiness": "happy",
            "sadness": "sad", "grief": "sad",
            "fear": "anxious", "nervousness": "anxious",
            "anger": "angry", "disgust": "angry",
            "surprise": "neutral", "neutral": "neutral",
        }
        try:
            results = self._transformer_pipeline(text[:512])[0]
            # results is a list of {label, score} dicts
            top = max(results, key=lambda r: r["score"])
            label = LABEL_MAP.get(top["label"].lower(), "neutral")
            return label, round(top["score"], 2)
        except Exception:
            return self._rule_based_detect(text.lower())


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    detector = EmotionDetector()
    samples = [
        "I feel so happy today, everything is going great!",
        "I am really sad and I don't know why",
        "Everyone is doing better than me. I'm such a failure.",
        "I'm so angry at my boss, this is completely unfair.",
        "I feel like no one really cares about me.",
        "I don't know what to do, there's too much going on.",
        "Just a normal day, nothing special.",
    ]
    for s in samples:
        emotion, conf = detector.detect(s)
        print(f"  [{emotion:10s} | {conf:.2f}]  {s[:60]}")
