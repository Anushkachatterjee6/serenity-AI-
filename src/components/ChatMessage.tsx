import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import { motion } from "framer-motion";
import { Square, Volume2 } from "lucide-react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

const TTS_LANGUAGES = [
  { code: "en-US", label: "EN" },
  { code: "hi-IN", label: "HI" },
  { code: "ta-IN", label: "TA" },
];

const markdownToSpeechText = (input: string) =>
  input
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[#>*_~\-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

const ChatMessage = ({ message, isStreaming }: ChatMessageProps) => {
  const isUser = message.role === "user";
  const [speakingLang, setSpeakingLang] = useState<string | null>(null);

  const speechText = useMemo(() => markdownToSpeechText(message.content), [message.content]);

  const stopSpeaking = () => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    setSpeakingLang(null);
  };

  const speakInLanguage = (lang: string) => {
    if (!speechText || typeof window === "undefined" || !window.speechSynthesis) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.lang = lang;
    utterance.rate = 1;
    utterance.pitch = 1;

    const voices = window.speechSynthesis.getVoices();
    const matchedVoice = voices.find((voice) => voice.lang.toLowerCase().startsWith(lang.toLowerCase()));
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onstart = () => setSpeakingLang(lang);
    utterance.onend = () => setSpeakingLang(null);
    utterance.onerror = () => setSpeakingLang(null);

    window.speechSynthesis.speak(utterance);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
    >
      <div
        className={`max-w-[80%] md:max-w-[70%] rounded-2xl px-5 py-3.5 ${
          isUser
            ? "bg-user-bubble text-user-bubble-foreground rounded-br-md"
            : "bg-ai-bubble text-ai-bubble-foreground rounded-bl-md shadow-sm border border-border"
        }`}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed">{message.content}</p>
        ) : (
          <div>
            <div className="prose prose-sm max-w-none text-ai-bubble-foreground prose-p:leading-relaxed prose-p:mb-2 last:prose-p:mb-0">
              <ReactMarkdown>{message.content}</ReactMarkdown>
              {isStreaming && (
                <span className="inline-block w-1.5 h-4 bg-primary/50 rounded-full animate-breathe ml-0.5 align-middle" />
              )}
            </div>

            {!isStreaming && (
              <div className="mt-2 flex items-center gap-1.5">
                {TTS_LANGUAGES.map((lang) => {
                  const isActive = speakingLang === lang.code;
                  return (
                    <button
                      key={lang.code}
                      onClick={() => speakInLanguage(lang.code)}
                      className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs border transition-colors ${
                        isActive
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-background/50 hover:bg-background border-border"
                      }`}
                      aria-label={`Play speech in ${lang.label}`}
                    >
                      <Volume2 className="h-3.5 w-3.5" />
                      {lang.label}
                    </button>
                  );
                })}
                {speakingLang && (
                  <button
                    onClick={stopSpeaking}
                    className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs border bg-background/50 hover:bg-background border-border"
                    aria-label="Stop speech"
                  >
                    <Square className="h-3 w-3" />
                    Stop
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default ChatMessage;
