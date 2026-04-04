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
    const { messages } = await req.json();
    const AI_GATEWAY_API_KEY = Deno.env.get("AI_GATEWAY_API_KEY");
    const AI_GATEWAY_URL = Deno.env.get("AI_GATEWAY_URL") ?? "https://openrouter.ai/api/v1/chat/completions";
    if (!AI_GATEWAY_API_KEY) throw new Error("AI_GATEWAY_API_KEY is not configured");

    const response = await fetch(AI_GATEWAY_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${AI_GATEWAY_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-3-flash-preview",
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          ...messages,
        ],
        stream: true,
      }),
    });

    if (!response.ok) {
      if (response.status === 429) {
        return new Response(JSON.stringify({ error: "Rate limits exceeded, please try again later." }), {
          status: 429,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      if (response.status === 402) {
        return new Response(JSON.stringify({ error: "Usage limit reached. Please add credits." }), {
          status: 402,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      const t = await response.text();
      console.error("AI gateway error:", response.status, t);
      return new Response(JSON.stringify({ error: "AI gateway error" }), {
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
