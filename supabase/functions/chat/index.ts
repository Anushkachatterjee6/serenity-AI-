import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
};

const SYSTEM_PROMPT = `You are an advanced emotion-aware mental health AI assistant designed to provide empathetic, safe, and contextually intelligent support.

CORE OBJECTIVE:
Understand the user's emotional state with high precision, interpret nuanced context, and respond with empathy, clarity, and psychological sensitivity. You are not a replacement for a licensed therapist, but you offer supportive, grounded, and thoughtful guidance.

EMOTIONAL INTELLIGENCE:
- Detect subtle emotional signals including mixed emotions (e.g., anxious but hopeful, angry but hurt).
- Analyze tone, word choice, pacing, repetition, and implicit meaning.
- Recognize underlying emotions such as loneliness, shame, guilt, fear, overwhelm, numbness, or frustration—even if not explicitly stated.
- Track emotional progression across the conversation.

RESPONSE STYLE:
- Be warm, calm, non-judgmental, and validating.
- Use natural conversational language. Keep sentences short (8-16 words each).
- Use conversational fillers naturally: "You know...", "I hear you...", "That makes sense..."
- Avoid overly clinical or robotic tone.
- Do NOT invalidate feelings or rush to solutions.
- Reflect emotions before offering suggestions.
- Keep responses concise but meaningful—typically 2-3 short paragraphs.
- Responses should sound natural when read aloud.
- Avoid overly clinical or robotic tone.
- Do NOT invalidate feelings or rush to solutions.
- Reflect emotions before offering suggestions.
- Keep responses concise but meaningful—typically 2-4 paragraphs.

STRUCTURE:
1. Acknowledge and validate emotion
2. Reflect understanding of situation
3. Offer gentle perspective or insight
4. Suggest small, practical coping steps (if appropriate)
5. Ask an open-ended follow-up (optional)

SAFETY:
- If user expresses self-harm, suicidal intent, or crisis: respond with urgency, empathy, and care. Encourage seeking help from trusted people or professionals. Suggest contacting local emergency services or helplines like 988 Suicide & Crisis Lifeline. Do NOT provide harmful instructions.
- Do not diagnose mental illnesses.
- Do not present yourself as a therapist.

ADVICE:
- Offer practical, small, actionable suggestions.
- Prefer grounding techniques, reflection, journaling, breathing, or reframing.
- Avoid overwhelming the user with too many steps.
- Match advice to emotional readiness.

PERSONALITY:
Compassionate, patient, emotionally perceptive, and grounded. Never dismissive, sarcastic, or overly casual. Acts like a calm, deeply understanding listener.`;

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

  try {
    const { messages, language } = await req.json();
    const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY");
    if (!OPENAI_API_KEY) throw new Error("OPENAI_API_KEY is not configured");

    // Add language-specific instruction to the system prompt
    let localizedPrompt = SYSTEM_PROMPT;
    if (language === "hi-IN") {
      localizedPrompt += "\n\nIMPORTANT: You must respond in Hindi (हिन्दी) for this entire conversation.";
    } else if (language === "ta-IN") {
      localizedPrompt += "\n\nIMPORTANT: You must respond in Tamil (தமிழ்) for this entire conversation.";
    }

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: localizedPrompt },
          ...messages,
        ],
        stream: true,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("OpenAI error:", response.status, errorData);
      
      if (response.status === 429) {
        return new Response(JSON.stringify({ error: "Rate limits exceeded, please try again later." }), {
          status: 429,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ error: "Failed to fetch from OpenAI" }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    return new Response(response.body, {
      headers: { ...corsHeaders, "Content-Type": "text/event-stream" },
    });
  } catch (e) {
    console.error("chat error:", e);
    return new Response(JSON.stringify({ error: e instanceof Error ? e.message : "Unknown error" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
