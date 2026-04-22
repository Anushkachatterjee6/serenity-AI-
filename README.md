# Serenity AI

A safe-space conversational assistant for mental wellness with text and voice support.


[![Live Demo](https://img.shields.io/badge/Live%20Demo-Aura-blue?style=for-the-badge)](https://serenitymentalhealthai.streamlit.app/)

## Description

Serenity AI offers an empathetic chat interface backed by Supabase Edge Functions and streamed AI responses. It is designed to provide calm, supportive conversational experiences with speech-to-text input and text-to-speech output.

## Features

- Empathetic mental wellness chat assistant
- Streamed AI responses via Supabase Edge Function
- Voice input using ElevenLabs realtime transcription
- Text-to-speech support in multiple languages
- Friendly welcome prompts and safe-space UI
- Crisis support banner with emergency contact info

## Tech Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Radix UI
- Backend: Supabase Edge Functions with Deno
- Speech and AI: ElevenLabs realtime transcription, OpenRouter/Gemini AI gateway
- Python: Streamlit, Requests, SpeechRecognition, gTTS

# Welcome to Emoti Sense AI






## Backend setup

Create a `.env` file in the project root with your Supabase config:

```env
VITE_SUPABASE_PROJECT_ID="your-project-id"
VITE_SUPABASE_PUBLISHABLE_KEY="your-supabase-anon-key"
VITE_SUPABASE_URL="https://your-project-id.supabase.co"
```

The Streamlit app reads these values and sends chat requests to:

```text
${VITE_SUPABASE_URL}/functions/v1/chat
```

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open `http://localhost:8501`

## Frontend setup

If you want to run the web client locally, install dependencies and start Vite:

```powershell
npm install
npm run dev
```

The frontend uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` to connect to Supabase and invoke the backend functions.

## Project structure

- `src/` — React app, pages, components, and Supabase integration
- `supabase/functions/` — serverless chat and ElevenLabs token functions
- `streamlit_app.py` — optional Python frontend for Streamlit
- `package.json` — frontend dependencies and scripts
- `requirements.txt` — Python dependencies for Streamlit

## Backend function secrets

The deployed Supabase Edge Functions also need these server-side secrets in Supabase:

```text
AI_GATEWAY_API_KEY
AI_GATEWAY_URL
ELEVENLABS_API_KEY
```
