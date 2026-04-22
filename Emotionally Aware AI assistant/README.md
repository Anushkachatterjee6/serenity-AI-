# ✦ Serenity — Emotion-Aware Mental Health AI Assistant


[![Live Demo](https://img.shields.io/badge/Live%20Demo-Aura-blue?style=for-the-badge)](https://serenitymentalhealthai.streamlit.app/)

A production-level Python application that provides empathetic, context-aware mental health support using NLP-based emotion detection and the Anthropic Claude API.

---

## 🌐 Live Demo
👉 https://serenitymentalhealthai.streamlit.app/

A production-level Python application that provides empathetic, context-aware mental health support using NLP-based emotion detection and the Anthropic Claude API.

---

## 📁 Project Structure

```
mental_health_ai/
├── main.py                # Entry point — wires all modules together
├── emotion_detector.py    # Detects explicit & implicit emotions
├── memory_engine.py       # Conversation history & emotion trajectory
├── response_generator.py  # Empathetic response generation (Claude API + fallback)
├── gui.py                 # Tkinter GUI
├── requirements.txt       # All dependencies
├── logs/                  # Auto-created — session logs stored here
└── README.md
```

---

## ⚙️ Installation

### Step 1 — Python
Ensure you have **Python 3.9+** installed.  
Download from: https://www.python.org/downloads/

### Step 2 — Create a virtual environment (recommended)
```bash
# In VS Code terminal (Ctrl+`)
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS / Linux)
source venv/bin/activate
```

### Step 3 — Install dependencies

#### Minimal install (rule-based + Claude API — recommended to start):
```bash
pip install anthropic SpeechRecognition pyttsx3
```

#### Full install (includes HuggingFace transformer model):
```bash
pip install anthropic SpeechRecognition pyttsx3 transformers torch
```

#### PyAudio (needed for microphone/voice input):
```bash
# Windows
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Ubuntu/Debian
sudo apt-get install python3-pyaudio
pip install pyaudio
```

> **Note**: `tkinter` is bundled with Python. If missing on Linux:
> `sudo apt-get install python3-tk`

---

## 🔑 Anthropic API Key Setup

Aura uses the Claude API for rich, empathetic responses.

1. Get your API key at: https://console.anthropic.com/
2. Set it as an environment variable:

```bash
# Windows (Command Prompt)
set ANTHROPIC_API_KEY=sk-ant-...

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."

# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or create a `.env` file in the project folder:
```
ANTHROPIC_API_KEY=sk-ant-...
```

> If no API key is set, Aura automatically falls back to the built-in rule-based response system — it still works fully offline.

---

## 🚀 Running the App in VS Code

1. Open the `mental_health_ai/` folder in VS Code
2. Open the integrated terminal: `Ctrl+`` (backtick)
3. Activate your virtual environment (see Step 2 above)
4. Run:

```bash
python main.py
```

The Aura GUI window will open.

---

## 🧠 How It Works

### Architecture Flow
```
User Input (text / voice)
        ↓
EmotionDetector
  • Keyword scoring (explicit emotions)
  • Regex pattern matching (implicit emotions)
  • Optional: HuggingFace transformer model
        ↓
MemoryEngine
  • Stores conversation history (last 50 turns)
  • Tracks emotion trajectory over time
  • Detects trends: improving / worsening / stable
  • Generates context summary for response generator
        ↓
ResponseGenerator  (Antigravity Protocol)
  • Priority 1: Conversation history + context
  • Priority 2: Emotion shift acknowledgment
  • Priority 3: Topic continuity
  • Priority 4: Claude API or rule-based fallback
        ↓
GUI (Tkinter)
  • Renders chat bubbles with typewriter animation
  • Shows emotion badge with confidence %
  • Typing indicator
  • Voice input + TTS output
  • Session save / reset
```

### Emotion Labels
| Label      | Example trigger                         |
|------------|-----------------------------------------|
| `happy`    | "I'm so excited today!"                 |
| `sad`      | "I've been crying all day"              |
| `anxious`  | "I can't stop worrying about everything"|
| `angry`    | "I'm so frustrated with my job"         |
| `lonely`   | "No one ever listens to me"             |
| `insecure` | "Everyone is doing better than me"      |
| `neutral`  | General / ambiguous messages            |
| `crisis`   | Any mention of self-harm / suicidal ideation |

### Crisis Handling
If crisis keywords are detected, Aura immediately provides crisis helpline numbers (India + international) and encourages the user to reach out for professional help.

---

## 🎙️ Voice Input
- Click the 🎤 microphone button
- Speak clearly — Aura listens for up to 8 seconds
- The transcribed text appears in the input box
- Press Enter or Send to submit

## 🔊 Text-to-Speech
- If `pyttsx3` is installed, Aura will read its responses aloud
- Runs in a background thread — won't block the UI

## 💾 Session Logging
- All conversations are saved automatically in `logs/`
- `.jsonl` files: line-by-line real-time logs
- `.json` files: full session snapshots (saved manually or on reset)

---

## 🔧 Customisation

### Enable HuggingFace Transformer (more accurate emotion detection)
In `main.py`, change:
```python
self.emotion_detector = EmotionDetector(use_transformer=False)
# to:
self.emotion_detector = EmotionDetector(use_transformer=True)
```
Requires `transformers` and `torch` to be installed, and internet access on first run.

### Add more emotion keywords
In `emotion_detector.py`, add words to the `EMOTION_KEYWORDS` dictionary.

### Adjust response tone
In `response_generator.py`, edit the `RESPONSES` dictionary to customise templates.

---

## ⚠️ Disclaimer

Aura is an AI companion for emotional support — it is **not** a replacement for professional mental health care. If you or someone you know is in crisis:

- **India**: iCall — 9152987821 | Vandrevala Foundation — 1860-2662-345
- **USA**: 988 Suicide & Crisis Lifeline — call or text **988**
- **UK**: Samaritans — 116 123
- **International**: https://www.iasp.info/resources/Crisis_Centres/
