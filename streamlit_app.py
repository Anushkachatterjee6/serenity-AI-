import hashlib
import json
import os
import tempfile
import base64
import time
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

import requests
import speech_recognition as sr
import streamlit as st
import streamlit.components.v1 as components
from gtts import gTTS


BACKEND_TIMEOUT_SECONDS = 60
FALLBACK_RESPONSE = "Backend not connected."

LANGUAGE_OPTIONS: Dict[str, Dict[str, str]] = {
    "English": {"stt": "en-IN", "tts": "en", "code": "en"},
    "Hindi": {"stt": "hi-IN", "tts": "hi", "code": "hi"},
    "Tamil": {"stt": "ta-IN", "tts": "ta", "code": "ta"},
}

PROXY_ENV_KEYS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "NO_PROXY",
    "no_proxy",
]


@contextmanager
def without_proxy_env():
    original = {key: os.environ.get(key) for key in PROXY_ENV_KEYS}
    try:
        for key in PROXY_ENV_KEYS:
            if key.lower().endswith("no_proxy"):
                os.environ[key] = "*"
            else:
                os.environ[key] = ""
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def load_dotenv_values(path: str = ".env") -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not os.path.exists(path):
        return values

    try:
        with open(path, "r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                values[key] = value
    except OSError:
        return values

    return values


DOTENV = load_dotenv_values()


def read_secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value).strip()


def get_config_value(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
        if key in DOTENV and DOTENV[key].strip():
            return DOTENV[key].strip()
        secret_value = read_secret(key)
        if secret_value:
            return secret_value
    return ""


def resolve_backend_url() -> str:
    explicit = get_config_value("BACKEND_URL")
    if explicit:
        return explicit

    supabase_url = get_config_value("VITE_SUPABASE_URL", "SUPABASE_URL")
    if supabase_url:
        return f"{supabase_url.rstrip('/')}/functions/v1/chat"
    return ""


def resolve_supabase_anon_key() -> str:
    return get_config_value("VITE_SUPABASE_PUBLISHABLE_KEY", "SUPABASE_ANON_KEY")


def parse_sse_response(response: requests.Response) -> str:
    chunks: List[str] = []
    for raw_line in response.iter_lines(decode_unicode=False):
        if not raw_line:
            continue

        if isinstance(raw_line, bytes):
            line = raw_line.decode("utf-8", errors="replace").strip()
        else:
            line = str(raw_line).strip()

        if line.startswith(":") or not line.startswith("data:"):
            continue
        payload = line[len("data:") :].strip()
        if payload == "[DONE]":
            break
        try:
            data = json.loads(payload)
        except ValueError:
            continue
        choice = data.get("choices", [{}])[0]
        delta = choice.get("delta", {}).get("content", "")
        if isinstance(delta, str) and delta.strip():
            chunks.append(delta)
            continue
        message = choice.get("message", {}).get("content", "")
        if isinstance(message, str) and message.strip():
            chunks.append(message)
    return "".join(chunks).strip()


def get_ai_response(messages: List[Dict[str, str]], user_text: str) -> Tuple[str, Optional[str]]:
    backend_url = resolve_backend_url()
    anon_key = resolve_supabase_anon_key()

    if not backend_url:
        return FALLBACK_RESPONSE, "No backend URL configured."

    headers = {"Content-Type": "application/json"}
    if anon_key:
        headers["Authorization"] = f"Bearer {anon_key}"
        headers["apikey"] = anon_key

    # Keep the required body { "text": text } while also supporting the existing backend { "messages": [...] }.
    payload = {"text": user_text, "messages": messages}

    try:
        with without_proxy_env():
            with requests.Session() as session:
                session.trust_env = False
                response = session.post(
                    backend_url,
                    json=payload,
                    headers=headers,
                    timeout=BACKEND_TIMEOUT_SECONDS,
                    stream=True,
                )
                response.encoding = "utf-8"
                response.raise_for_status()
    except requests.RequestException as error:
        return FALLBACK_RESPONSE, f"Backend request failed: {error}"

    content_type = response.headers.get("Content-Type", "")
    if "text/event-stream" in content_type:
        parsed = parse_sse_response(response)
        if parsed:
            return parsed, None
        return FALLBACK_RESPONSE, "Backend stream returned no content."

    try:
        data = response.json()
    except ValueError:
        text_value = response.text.strip()
        if text_value:
            return text_value, None
        return FALLBACK_RESPONSE, "Backend returned empty non-JSON response."

    if isinstance(data, dict):
        for key in ("response", "text", "message", "content"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip(), None
        try:
            choice_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if isinstance(choice_content, str) and choice_content.strip():
                return choice_content.strip(), None
        except Exception:
            pass

    return FALLBACK_RESPONSE, "Backend JSON shape not recognized."


def transcribe_audio(audio_bytes: bytes, stt_language: str) -> Tuple[Optional[str], Optional[str]]:
    recognizer = sr.Recognizer()
    temp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        with sr.AudioFile(temp_path) as source:
            audio_data = recognizer.record(source)
        with without_proxy_env():
            text = recognizer.recognize_google(audio_data, language=stt_language)
        if text and text.strip():
            return text.strip(), None
        return None, "Speech was captured but no text could be recognized."
    except sr.UnknownValueError:
        return None, "Speech was unclear. Please speak closer to the mic and try again."
    except sr.RequestError as error:
        return None, f"Speech service error: {error}"
    except Exception as error:
        return None, f"Audio processing failed: {error}"
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def text_to_speech_file(text: str, tts_language: str) -> Tuple[Optional[str], Optional[str]]:
    if not text.strip():
        return None, "No text to speak."
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            audio_path = temp_file.name
        with without_proxy_env():
            gTTS(text=text, lang=tts_language).save(audio_path)
        return audio_path, None
    except Exception as error:
        return None, f"TTS generation failed: {error}"


def cleanup_previous_audio() -> None:
    old_path = st.session_state.get("latest_audio_path")
    if old_path and isinstance(old_path, str) and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except OSError:
            pass
    st.session_state.latest_audio_path = None


def stop_all_audio() -> None:
    components.html(
        """
        <script>
        (function () {
          if (window.speechSynthesis) {
            try { window.speechSynthesis.cancel(); } catch (e) {}
          }
          const media = document.querySelectorAll("audio[id^='auto-audio-']");
          media.forEach((a) => {
            try {
              a.pause();
              a.currentTime = 0;
              a.removeAttribute("src");
              a.load();
            } catch (e) {}
          });
        })();
        </script>
        """,
        height=0,
    )


def autoplay_hidden_audio(audio_path: str) -> None:
    try:
        with open(audio_path, "rb") as file:
            encoded = base64.b64encode(file.read()).decode("ascii")
    except OSError:
        return

    audio_id = f"auto-audio-{int(time.time() * 1000)}"
    components.html(
        f"""
        <audio id="{audio_id}" autoplay style="display:none">
          <source src="data:audio/mp3;base64,{encoded}" type="audio/mp3">
        </audio>
        <script>
        (function () {{
          const el = document.getElementById("{audio_id}");
          if (!el) return;
          const p = el.play();
          if (p && typeof p.then === "function") {{
            p.catch(() => {{}});
          }}
        }})();
        </script>
        """,
        height=0,
    )


def autoplay_browser_tts(text: str, tts_web_language: str) -> None:
    if not text.strip():
        return
    escaped_text = json.dumps(text)
    escaped_lang = json.dumps(tts_web_language)
    components.html(
        f"""
        <script>
        (function () {{
          if (!window.speechSynthesis) return;
          try {{
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance({escaped_text});
            utter.lang = {escaped_lang};
            utter.rate = 1.0;
            utter.pitch = 1.0;

            const pickVoice = () => {{
              const voices = window.speechSynthesis.getVoices() || [];
              const wanted = {escaped_lang}.toLowerCase();
              const exact = voices.find(v => (v.lang || '').toLowerCase() === wanted);
              const starts = voices.find(v => (v.lang || '').toLowerCase().startsWith(wanted.split('-')[0]));
              if (exact) utter.voice = exact;
              else if (starts) utter.voice = starts;
            }};

            pickVoice();
            window.speechSynthesis.onvoiceschanged = pickVoice;
            window.speechSynthesis.speak(utter);
          }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
    )
def process_user_message(user_text: str, tts_language: str, tts_web_language: str, mute: bool) -> None:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            assistant_text, backend_error = get_ai_response(st.session_state.messages, user_text)
        st.markdown(assistant_text)
        if backend_error:
            st.caption(f"Backend note: {backend_error}")
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

        cleanup_previous_audio()
        if not mute:
            # Single playback path: browser TTS to avoid duplicate voices.
            autoplay_browser_tts(assistant_text, tts_web_language)


st.set_page_config(page_title="Emotion-Aware Mental Health AI Assistant", layout="centered")

st.markdown(
    """
    <style>
      .stApp {
        background:
          radial-gradient(1000px 500px at -10% -20%, rgba(20,90,180,0.22), transparent 60%),
          radial-gradient(900px 500px at 110% -10%, rgba(30,180,140,0.16), transparent 60%),
          #040a16;
      }
      .main .block-container {
        max-width: 920px;
        padding-top: 1.25rem;
      }
      .hero-wrap {
        border: 1px solid rgba(255,255,255,0.10);
        background: linear-gradient(135deg, rgba(10,18,35,0.86), rgba(17,30,58,0.86));
        border-radius: 16px;
        padding: 16px 18px;
        margin-bottom: 0.75rem;
      }
      .hero-title {
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: 0.2px;
        color: #e9f1ff;
        margin: 0;
      }
      .hero-sub {
        margin: 0.25rem 0 0 0;
        color: #a9c0e8;
        font-size: 0.92rem;
      }
      .stSelectbox, .stToggle {
        background: rgba(10, 17, 30, 0.55);
        border-radius: 12px;
        padding: 6px 8px;
      }
      .stChatMessage {
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(8, 15, 30, 0.68);
        backdrop-filter: blur(3px);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-wrap">
      <p class="hero-title">Emotion-Aware Mental Health AI Assistant</p>
      <p class="hero-sub">Talk naturally in English, Hindi, or Tamil with voice + text support.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_language = st.selectbox("Language", list(LANGUAGE_OPTIONS.keys()), index=0)
mute = st.toggle("Mute Voice")

if mute:
    stop_all_audio()

resolved_backend_url = resolve_backend_url()
if resolved_backend_url:
    st.caption(f"Backend endpoint: {resolved_backend_url}")
else:
    st.warning("Backend URL not configured. Set BACKEND_URL (or VITE_SUPABASE_URL) to connect.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "latest_audio_path" not in st.session_state:
    st.session_state.latest_audio_path = None
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = ""
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = ""

lang_config = LANGUAGE_OPTIONS[selected_language]

st.caption("Speech to text input")
audio_input = st.audio_input("Use microphone")
if audio_input is not None:
    audio_bytes = audio_input.getvalue()
    current_hash = hashlib.sha256(audio_bytes).hexdigest()
    if current_hash != st.session_state.last_audio_hash:
        transcript, stt_error = transcribe_audio(audio_bytes, lang_config["stt"])
        st.session_state.last_audio_hash = current_hash
        if transcript:
            st.session_state.pending_prompt = transcript
            st.success(f"Transcribed: {transcript}")
        else:
            st.warning("Could not transcribe audio. Please try again.")
            if stt_error:
                st.caption(f"STT note: {stt_error}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

typed_prompt = st.chat_input("Share what's on your mind...")
voice_prompt = st.session_state.pending_prompt.strip()
if voice_prompt:
    st.session_state.pending_prompt = ""

user_prompt = ""
if typed_prompt and typed_prompt.strip():
    user_prompt = typed_prompt.strip()
elif voice_prompt:
    user_prompt = voice_prompt

if user_prompt:
    tts_web_lang = {
        "en": "en-IN",
        "hi": "hi-IN",
        "ta": "ta-IN",
    }.get(lang_config["code"], "en-IN")
    process_user_message(user_prompt, lang_config["tts"], tts_web_lang, mute)
