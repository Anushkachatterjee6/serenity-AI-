import { useState, useRef, useCallback, KeyboardEvent, useEffect } from "react";
import { SendHorizontal, Mic, MicOff, Loader2, Globe } from "lucide-react";
import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const LANGUAGES = [
  { code: "en-US", label: "English" },
  { code: "hi-IN", label: "हिन्दी" },
  { code: "ta-IN", label: "தமிழ்" },
];

interface ChatInputProps {
  onSend: (message: string, lang: string) => void;
  disabled?: boolean;
}

const ChatInput = ({ onSend, disabled }: ChatInputProps) => {
  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [language, setLanguage] = useState("en-US");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);
  const isProcessingRef = useRef(false);
  const accumulationRef = useRef(""); // Stores finalized text before the current result

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true; // Allow long pauses
      recognition.interimResults = true; // Show text as user speaks
      
      recognition.onresult = (event: any) => {
        let interimTranscript = "";
        let finalTranscript = "";

        // Iterate through all results to build the full transcript
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        if (finalTranscript) {
          accumulationRef.current += (accumulationRef.current ? " " : "") + finalTranscript.trim();
        }

        // Update the visible input with finalized accumulation + current interim
        const currentTotal = (accumulationRef.current + " " + interimTranscript).trim();
        if (currentTotal) {
          setInput(currentTotal);
          autoResize();
        }
      };

      recognition.onerror = (event: any) => {
        console.error("Speech recognition error:", event.error);
        if (event.error !== "no-speech") {
          toast.error("Voice input error. Please try again.");
        }
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    } catch (e) {
      console.error("Failed to initialize SpeechRecognition:", e);
    }
    
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch { /* ignore */ }
      }
    };
  }, []);

  const autoResize = () => {
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (el) {
        el.style.height = "auto";
        el.style.height = Math.min(el.scrollHeight, 150) + "px";
      }
    });
  };

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    
    // Stop recording if active
    if (isRecording) {
      recognitionRef.current?.stop();
    }
    
    onSend(trimmed, language);
    setInput("");
    accumulationRef.current = "";
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    
    // Cancel TTS when user sends a new message
    window.speechSynthesis.cancel();
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
      el.style.height = Math.min(el.scrollHeight, 150) + "px";
    }
    // Cancel TTS when user starts typing
    window.speechSynthesis.cancel();
  };

  const toggleRecording = useCallback(() => {
    if (!recognitionRef.current) {
      toast.error("Speech recognition is not supported in this browser.");
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      return;
    }

    // Reset accumulation for new recording session
    accumulationRef.current = input.trim();
    
    // Cancel TTS when user starts recording
    window.speechSynthesis.cancel();
    
    try {
      recognitionRef.current.lang = language;
      recognitionRef.current.start();
      setIsRecording(true);
    } catch (e) {
      console.error("STT start error:", e);
      setIsRecording(false);
    }
  }, [isRecording, language, input]);

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
          disabled={disabled}
          className={`flex-shrink-0 h-10 w-10 rounded-xl flex items-center justify-center transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
            isRecording
              ? "bg-destructive text-destructive-foreground animate-pulse"
              : "bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80"
          }`}
          aria-label={isRecording ? "Stop recording" : "Start voice input"}
        >
          {isRecording ? (
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
          placeholder={isRecording ? "Listening… speak now" : "Share what's on your mind..."}
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
          🎙️ Listening in {LANGUAGES.find((l) => l.code === language)?.label}…
        </p>
      )}
    </div>
  );
};

export default ChatInput;
