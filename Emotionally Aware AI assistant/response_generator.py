"""
response_generator.py
----------------------
Generates empathetic, context-aware responses using the Anthropic Claude API.
Falls back to a rich rule-based system if the API is unavailable.
Implements the "Antigravity Prompt" concept for topic continuity and
dynamic emotional tracking.
"""

import random
import re
from typing import List, Optional

from memory_engine import MemoryEngine, Message


# ---------------------------------------------------------------------------
# Rule-based response templates  (fallback / offline mode)
# ---------------------------------------------------------------------------

RESPONSES: dict = {
    "crisis": [
        "I'm really glad you reached out. What you're feeling matters deeply. "
        "Please know that you're not alone — help is available right now. "
        "If you're in immediate danger, please call a crisis helpline: "
        "iCall (India): 9152987821 | Vandrevala Foundation: 1860-2662-345 | "
        "International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/. "
        "I'm here with you. Would you like to tell me a little about what's been going on?",
    ],

    "happy": [
        "That's wonderful to hear! ✨ What's been making you feel so good?",
        "I love hearing that! It sounds like things are going really well for you. Tell me more!",
        "That genuinely made me smile. What's been the highlight of your day?",
        "You deserve to feel this way! What's been lifting your spirits?",
    ],

    "sad": [
        "I'm really sorry you're feeling this way. Sadness can feel so heavy sometimes. "
        "I'm here and I'm listening — would you like to share what's been weighing on you?",
        "That sounds really painful. You don't have to carry this alone. "
        "What's been going on for you lately?",
        "I hear you, and I'm glad you're talking about it. "
        "Sometimes just saying things out loud can help. What's on your mind?",
        "It takes courage to acknowledge how you're feeling. "
        "I'm here with you. Can you tell me more about what's been happening?",
    ],

    "anxious": [
        "Anxiety can feel so overwhelming, and I really hear that in what you're saying. "
        "You're not alone in this. Can you tell me what's been worrying you the most?",
        "That sounds incredibly stressful. Let's slow down together for a moment — "
        "take a breath. What feels most urgent to you right now?",
        "It's okay to feel anxious. What you're feeling is valid. "
        "What's been on your mind the most lately?",
        "I can sense you're carrying a lot right now. "
        "What would feel most helpful — talking through your worries, or just being heard?",
    ],

    "angry": [
        "That frustration sounds completely real. "
        "What happened that made you feel this way?",
        "I hear the anger in your words, and it makes sense given what you're going through. "
        "Do you want to vent, or would you like help thinking through the situation?",
        "Sometimes anger is how pain shows up. You have every right to feel what you feel. "
        "Tell me more about what's been going on.",
        "It sounds like something really got under your skin. "
        "I'm listening — what happened?",
    ],

    "lonely": [
        "Feeling lonely can be one of the most painful experiences. "
        "I want you to know I'm right here, and I care about what you're going through. "
        "Can you tell me more about what's been making you feel this way?",
        "That sense of not being seen or valued is so hard to carry. "
        "You're not invisible to me — I'm listening. What's been happening?",
        "Loneliness can feel like a wall between you and the rest of the world. "
        "Would you like to talk about what's been isolating you?",
        "I hear you. Sometimes the loneliest moments are the ones we carry silently. "
        "I'm glad you shared this with me. Tell me more.",
    ],

    "insecure": [
        "Comparing ourselves to others is something so many people struggle with, "
        "and it can be really painful. What's been making you feel this way about yourself?",
        "Those feelings of not measuring up are real and they hurt. "
        "But I want to gently remind you: comparison often only shows us someone else's highlights. "
        "What's been going on?",
        "It sounds like you've been really hard on yourself lately. "
        "I'm curious — what would you say to a close friend who felt the same way you do?",
        "Feeling like you're falling behind is exhausting. "
        "Let's talk about what's been stirring this up for you.",
    ],

    "neutral": [
        "I'm here and happy to chat. How has your day been going?",
        "Thanks for sharing that with me. "
        "Is there something specific on your mind today?",
        "I'm listening. What would you like to talk about?",
        "How are you feeling right now, beyond the surface level?",
    ],
}

# Acknowledgment phrases that reference prior context
CONTINUITY_PHRASES = [
    "Building on what you shared earlier",
    "Given what you told me before",
    "You mentioned this before, and I want to revisit it",
    "This connects to what you shared a moment ago",
    "Thinking about what you've told me so far",
]

# Transition phrases for emotion shifts
SHIFT_POSITIVE = [
    "I notice things seem a bit lighter for you now. That's really good to see.",
    "It sounds like something may have shifted a little — am I reading that right?",
    "There seems to be a small but real change in how you're feeling. I'm glad.",
]

SHIFT_NEGATIVE = [
    "I notice things might be feeling harder right now than a moment ago. I'm with you.",
    "It sounds like this is weighing on you more deeply. Thank you for letting me know.",
    "I can hear that things have gotten heavier. I'm not going anywhere.",
]

WORSENING_EXTRA_CARE = [
    "I've noticed our conversation has been heavy, and I want to check in — "
    "how are you really doing right now?",
    "You've been carrying a lot in this conversation. I'm genuinely concerned about you. "
    "Is there anything specific that would feel helpful right now?",
]

REPEATED_EMOTION_ACKNOWLEDGMENT = {
    "sad": "I've been sitting with you through some heavy feelings. "
           "I want you to know that reaching out matters, even when things feel dark.",
    "anxious": "You've been dealing with a lot of anxiety. "
               "It might help to focus on just one thing at a time. "
               "What feels most manageable to address right now?",
    "lonely": "You've been feeling disconnected for a while now. "
              "I want to ask — is there anyone in your life, even one person, "
              "you feel you could reach out to?",
    "angry": "There's been a lot of frustration building up. "
             "Sometimes it helps to name what's underneath the anger. "
             "What do you think is really hurting you?",
    "insecure": "You've been very hard on yourself through this conversation. "
                "I want to ask you something: what's one thing you're genuinely good at, "
                "no matter how small it seems?",
}


# ---------------------------------------------------------------------------
# Response Generator
# ---------------------------------------------------------------------------

class ResponseGenerator:
    """
    Generates empathetic, context-aware responses.
    Prioritises the Claude API for rich language generation,
    and falls back to a rule-based system.
    """

    def __init__(self, memory: MemoryEngine, use_api: bool = True):
        self.memory = memory
        self.use_api = use_api
        self._api_available = False

        if use_api:
            self._api_available = self._check_api()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, user_text: str, emotion: str, confidence: float) -> str:
        """
        Main entry point.  Returns a response string.
        """
        # Always check for crisis first
        if emotion == "crisis":
            return random.choice(RESPONSES["crisis"])

        # Try Claude API first
        if self._api_available:
            try:
                return self._api_response(user_text, emotion, confidence)
            except Exception as e:
                print(f"[ResponseGenerator] API error: {e}. Falling back to rule-based.")

        # Fall back to rule-based system
        return self._rule_based_response(user_text, emotion, confidence)

    # ------------------------------------------------------------------
    # Claude API response
    # ------------------------------------------------------------------

    def _check_api(self) -> bool:
        """Verify Anthropic package is importable."""
        try:
            import anthropic  # type: ignore  # noqa
            return True
        except ImportError:
            return False

    def _build_system_prompt(self) -> str:
        """Antigravity prompt: context-first, emotion-aware, topic-continuous."""
        trend = self.memory.get_emotion_trend()
        ctx_summary = self.memory.get_context_summary()

        return f"""You are a warm, deeply empathetic mental health support companion named "Aura".

Your role:
- Listen actively and respond with genuine care and understanding
- Reference the conversation history naturally — never ignore what was said before
- Adapt your tone to the user's current emotional state
- Avoid generic or repetitive responses
- Never give medical diagnoses or prescriptions
- If the user seems to be in crisis, always provide crisis resources
- Keep responses concise (2-4 sentences usually) unless the user needs more

Current conversation context:
{ctx_summary}

Current emotional trend: {trend['dominant']} (worsening={trend['worsening']}, improving={trend['improving']})

Response guidelines (Antigravity Protocol):
1. TOPIC CONTINUITY: Stay on the same topic the user raised unless they change it
2. EMOTION TRACKING: Acknowledge any shift in emotion since the last message
3. MEMORY PRIORITY: Weave in relevant past context naturally
4. CONSISTENCY: Don't contradict previous responses or forget what was shared
5. HUMAN-LIKE: Use natural language, occasional light affirmations, no clinical jargon

You are NOT a therapist and should gently remind the user to seek professional help when appropriate."""

    def _build_messages(self, user_text: str) -> list:
        """Build the messages array for the API call."""
        recent = self.memory.get_recent_history(n_turns=5)
        messages = []

        for msg in recent[:-1]:  # exclude the latest user msg (we'll add it fresh)
            messages.append({"role": msg.role, "content": msg.text})

        # Add current user message
        messages.append({"role": "user", "content": user_text})
        return messages

    def _api_response(self, user_text: str, emotion: str, confidence: float) -> str:
        """Call the Anthropic API."""
        import anthropic  # type: ignore

        client = anthropic.Anthropic()
        messages = self._build_messages(user_text)
        system_prompt = self._build_system_prompt()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system=system_prompt,
            messages=messages,
        )

        return response.content[0].text.strip()

    # ------------------------------------------------------------------
    # Rule-based fallback
    # ------------------------------------------------------------------

    def _rule_based_response(self, user_text: str, emotion: str, confidence: float) -> str:
        """
        Antigravity rule-based engine:
        1. Pick base response for emotion
        2. Prepend continuity/shift acknowledgment if needed
        3. Append follow-up question for engagement
        """
        parts = []

        # --- Emotion shift acknowledgment ---
        shift = self.memory.emotion_shifted()
        if shift:
            prev, curr = shift
            positive_emotions = {"happy", "neutral"}
            if prev not in positive_emotions and curr in positive_emotions:
                parts.append(random.choice(SHIFT_POSITIVE))
            elif curr not in positive_emotions and prev in positive_emotions:
                parts.append(random.choice(SHIFT_NEGATIVE))

        # --- Worsening trend: extra care ---
        trend = self.memory.get_emotion_trend()
        if trend["worsening"] and not self.memory.is_first_turn():
            parts.append(random.choice(WORSENING_EXTRA_CARE))
            return " ".join(parts)

        # --- Repeated emotion: special acknowledgment ---
        repeated = self.memory.get_repeated_emotion()
        if repeated and repeated in REPEATED_EMOTION_ACKNOWLEDGMENT:
            parts.append(REPEATED_EMOTION_ACKNOWLEDGMENT[repeated])
            return " ".join(parts)

        # --- Context continuity prefix (after turn 2) ---
        if not self.memory.is_first_turn() and random.random() < 0.35:
            parts.append(random.choice(CONTINUITY_PHRASES) + ",")

        # --- Base emotion response ---
        pool = RESPONSES.get(emotion, RESPONSES["neutral"])
        parts.append(random.choice(pool))

        return " ".join(parts)


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from memory_engine import MemoryEngine
    mem = MemoryEngine(log_dir="logs_test")
    gen = ResponseGenerator(mem, use_api=False)   # offline test

    turns = [
        ("I feel really sad today.", "sad", 0.8),
        ("Nobody seems to care about me.", "lonely", 0.9),
        ("I don't know what to do anymore.", "sad", 0.85),
        ("Maybe things will get better.", "neutral", 0.5),
    ]

    for text, emotion, conf in turns:
        mem.add_user_message(text, emotion, conf)
        response = gen.generate(text, emotion, conf)
        mem.add_assistant_message(response)
        print(f"User  [{emotion}]: {text}")
        print(f"Aura : {response}")
        print()
