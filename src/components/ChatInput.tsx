import { useState, useRef, useCallback, KeyboardEvent } from "react";
import { SendHorizontal, Mic, MicOff, Loader2, Globe } from "lucide-react";
import { useScribe, CommitStrategy } from "@elevenlabs/react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const LANGUAGES = [
  { code: "eng", label: "English" },
  { code: "hin", label: "हिन्दी" },
  { code: "tam", label: "தமிழ்" },
];

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const ChatInput = ({ onSend, disabled }: ChatInputProps) => {
  const [input, setInput] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [language, setLanguage] = useState("eng");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const baselineRef = useRef("");
  const committedRef = useRef("");
  const partialRef = useRef("");
  const lastCommitRef = useRef("");

  const autoResize = useCallback(() => {
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (el) {
        el.style.height = "auto";
        el.style.height = `${Math.min(el.scrollHeight, 150)}px`;
      }
    });
  }, []);

  const normalizeTranscript = (value: string) =>
    value
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s]/gu, "")
      .replace(/\s+/g, " ")
      .trim();

  const renderTranscript = useCallback(() => {
    const merged = [baselineRef.current, committedRef.current, partialRef.current]
      .map((v) => v.trim())
      .filter(Boolean)
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();
    setInput(merged);
    autoResize();
  }, [autoResize]);

  const clearTranscriptState = () => {
    baselineRef.current = "";
    committedRef.current = "";
    partialRef.current = "";
    lastCommitRef.current = "";
  };

  const scribe = useScribe({
    modelId: "scribe_v2_realtime",
    languageCode: language,
    commitStrategy: CommitStrategy.VAD,
    onPartialTranscript: (data) => {
      partialRef.current = (data.text ?? "").trim();
      renderTranscript();
    },
    onCommittedTranscript: (data) => {
      const committed = (data.text ?? "").trim();

      if (!committed) {
        partialRef.current = "";
        renderTranscript();
        return;
      }

      const normalizedIncoming = normalizeTranscript(committed);
      const normalizedExisting = normalizeTranscript(committedRef.current);

      // Some STT events are repeated or cumulative; this keeps one canonical transcript.
      if (normalizedIncoming && normalizedIncoming === lastCommitRef.current) {
        partialRef.current = "";
        renderTranscript();
        return;
      }

      if (normalizedIncoming.startsWith(normalizedExisting) && normalizedExisting.length > 0) {
        committedRef.current = committed;
      } else if (
        normalizedIncoming === normalizedExisting ||
        normalizedExisting.endsWith(normalizedIncoming)
      ) {
        // Duplicate commit event, ignore it.
      } else {
        committedRef.current = [committedRef.current, committed]
          .map((v) => v.trim())
          .filter(Boolean)
          .join(" ");
      }

      lastCommitRef.current = normalizedIncoming;
      partialRef.current = "";
      renderTranscript();
    },
  });

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;

    if (scribe.isConnected) {
      scribe.disconnect();
    }

    onSend(trimmed);
    setInput("");
    clearTranscriptState();

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 150)}px`;
    }
  };

  const toggleRecording = useCallback(async () => {
    if (scribe.isConnected) {
      scribe.disconnect();
      return;
    }

    setIsConnecting(true);
    try {
      const { data, error } = await supabase.functions.invoke("elevenlabs-scribe-token");

      if (error || !data?.token) {
        throw new Error("Could not get transcription token");
      }

      baselineRef.current = input.trim();
      committedRef.current = "";
      partialRef.current = "";
      lastCommitRef.current = "";

      await scribe.connect({
        token: data.token,
        microphone: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
    } catch (e) {
      console.error("STT error:", e);
      toast.error("Could not start voice input. Please check microphone permissions.");
    } finally {
      setIsConnecting(false);
    }
  }, [input, scribe]);

  const isRecording = scribe.isConnected;

  return (
    <div className="border-t border-border bg-card px-4 py-3">
      <div className="max-w-2xl mx-auto flex items-end gap-2">
        <Select value={language} onValueChange={setLanguage} disabled={isRecording}>
          <SelectTrigger className="w-[100px] h-10 rounded-xl bg-muted border-0 text-xs flex-shrink-0">
            <Globe className="h-3.5 w-3.5 mr-1 flex-shrink-0" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {LANGUAGES.map((lang) => (
              <SelectItem key={lang.code} value={lang.code}>
                {lang.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <button
          onClick={toggleRecording}
          disabled={disabled || isConnecting}
          className={`flex-shrink-0 h-10 w-10 rounded-xl flex items-center justify-center transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
            isRecording
              ? "bg-destructive text-destructive-foreground animate-pulse"
              : "bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80"
          }`}
          aria-label={isRecording ? "Stop recording" : "Start voice input"}
        >
          {isConnecting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : isRecording ? (
            <MicOff className="h-4 w-4" />
          ) : (
            <Mic className="h-4 w-4" />
          )}
        </button>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            handleInput();
          }}
          onKeyDown={handleKeyDown}
          placeholder={isRecording ? "Listening... speak now" : "Share what's on your mind..."}
          rows={1}
          disabled={disabled}
          className="flex-1 resize-none bg-muted rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/30 transition-all disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="flex-shrink-0 h-10 w-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <SendHorizontal className="h-4 w-4" />
        </button>
      </div>
      {isRecording && (
        <p className="max-w-2xl mx-auto mt-1.5 text-xs text-muted-foreground text-center">
          Listening in {LANGUAGES.find((l) => l.code === language)?.label}...
        </p>
      )}
    </div>
  );
};

export default ChatInput;
