import { useState, useRef, useEffect, useCallback } from "react";
import { Leaf, Volume2, VolumeX } from "lucide-react";
import CrisisBanner from "@/components/CrisisBanner";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import WelcomeScreen from "@/components/WelcomeScreen";
import { toast } from "sonner";

type Message = {
  role: "user" | "assistant";
  content: string;
};



const Index = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastLangRef = useRef("en-US");

  // Ensure voices are loaded (browsers like Chrome load them asynchronously)
  useEffect(() => {
    const handleVoicesChanged = () => {
      window.speechSynthesis.getVoices();
    };
    window.speechSynthesis.addEventListener("voiceschanged", handleVoicesChanged);
    // Initial call to populate voices
    window.speechSynthesis.getVoices();
    return () => window.speechSynthesis.removeEventListener("voiceschanged", handleVoicesChanged);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const speak = useCallback((text: string, lang?: string) => {
    if (isMuted) return;
    
    const targetLang = lang || lastLangRef.current;
    
    // Exactly replicating the "OPTION 1 (BEST)" snippet provided
    if (targetLang.startsWith("ta")) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const voices = window.speechSynthesis.getVoices();
      
      const tamilVoice = voices.find(v => 
        v.lang === "ta-IN" || v.name.toLowerCase().includes("tamil")
      );
      
      if (tamilVoice) {
        utterance.voice = tamilVoice;
      }
      
      utterance.lang = "ta-IN";
      window.speechSynthesis.speak(utterance);
      return;
    }
    
    // Standard local Web Speech API for English, Hindi, etc.
    window.speechSynthesis.cancel();
    const voices = window.speechSynthesis.getVoices();
    const langBase = targetLang.split("-")[0].toLowerCase();
    const langNames: Record<string, string> = { "hi": "hindi", "en": "english" };
    const langName = langNames[langBase];
    
    const sentences = text.match(/[^.!?।॥\n]+[.!?।॥\n]*/g) || [text];
    
    sentences.forEach(sentence => {
      if (!sentence.trim()) return;
      
      const utterance = new SpeechSynthesisUtterance(sentence.trim());
      
      const matchedVoice = voices.find(v => 
        v.lang === targetLang || 
        (langName && v.name.toLowerCase().includes(langName))
      );
      
      if (matchedVoice) {
        utterance.voice = matchedVoice;
      }
      
      utterance.lang = targetLang;
      window.speechSynthesis.speak(utterance);
    });
  }, [isMuted]);

  const sendMessage = useCallback(async (input: string, lang: string = "en-US") => {
    // Unlock audio context on user interaction
    const unlockUtterance = new SpeechSynthesisUtterance("");
    unlockUtterance.volume = 0;
    window.speechSynthesis.speak(unlockUtterance);
    
    lastLangRef.current = lang;
    const userMsg: Message = { role: "user", content: input };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setIsLoading(true);

    let assistantSoFar = "";

    const upsertAssistant = (chunk: string) => {
      assistantSoFar += chunk;
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last?.role === "assistant") {
          return prev.map((m, i) => (i === prev.length - 1 ? { ...m, content: assistantSoFar } : m));
        }
        return [...prev, { role: "assistant", content: assistantSoFar }];
      });
    };

    try {
      const resp = await fetch("%%SUPABASE_URL%%/functions/v1/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer %%SUPABASE_KEY%%`,
        },
        body: JSON.stringify({ 
          messages: updatedMessages,
          language: lang 
        }),
      });

      if (!resp.ok) {
        if (resp.status === 429) {
          toast.error("Taking a moment to breathe — please try again shortly.");
        } else {
          toast.error("Something went wrong. Please try again.");
        }
        setIsLoading(false);
        return;
      }

      if (!resp.body) throw new Error("No response body");

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let textBuffer = "";
      let streamDone = false;

      while (!streamDone) {
        const { done, value } = await reader.read();
        if (done) break;
        textBuffer += decoder.decode(value, { stream: true });

        let newlineIndex: number;
        while ((newlineIndex = textBuffer.indexOf("\n")) !== -1) {
          let line = textBuffer.slice(0, newlineIndex);
          textBuffer = textBuffer.slice(newlineIndex + 1);

          if (line.endsWith("\r")) line = line.slice(0, -1);
          if (line.startsWith(":") || line.trim() === "") continue;
          if (!line.startsWith("data: ")) continue;

          const jsonStr = line.slice(6).trim();
          if (jsonStr === "[DONE]") {
            streamDone = true;
            break;
          }

          try {
            const parsed = JSON.parse(jsonStr);
            const content = parsed.choices?.[0]?.delta?.content;
            if (content) upsertAssistant(content);
          } catch (e) {
            // Keep the line in the buffer if it's incomplete
            textBuffer = line + "\n" + textBuffer;
            break;
          }
        }
      }
      
      // Final flush of residue in buffer
      if (textBuffer.trim()) {
        const lines = textBuffer.split("\n");
        for (let line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();
            if (data === "[DONE]") continue;
            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices?.[0]?.delta?.content;
              if (content) upsertAssistant(content);
            } catch { /* ignore final partials */ }
          }
        }
      }
      
      // Speak the final response
      if (assistantSoFar) {
        speak(assistantSoFar);
      }

    } catch (e) {
      console.error(e);
      toast.error("Connection lost. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, [messages, speak]);

  const toggleMute = () => {
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    if (newMuted) {
      window.speechSynthesis.cancel();
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="flex flex-col h-screen bg-background">
      <CrisisBanner />

      {/* Header */}
      <header className="border-b border-border bg-card px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-sage-light flex items-center justify-center">
              <Leaf className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-display text-base font-semibold text-foreground leading-tight">Serenity</h2>
              <p className="text-xs text-muted-foreground">Your safe space to talk</p>
            </div>
          </div>
          <button
            onClick={toggleMute}
            className="h-10 w-10 flex items-center justify-center rounded-xl bg-muted text-muted-foreground hover:text-foreground transition-colors"
            title={isMuted ? "Unmute AI" : "Mute AI"}
          >
            {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          </button>
        </div>
      </header>

      {/* Chat area */}
      {hasMessages ? (
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-2xl mx-auto">
            {messages.map((msg, i) => (
              <ChatMessage
                key={i}
                message={msg}
                isStreaming={isLoading && i === messages.length - 1 && msg.role === "assistant"}
              />
            ))}
          </div>
        </div>
      ) : (
        <WelcomeScreen onStart={sendMessage} />
      )}

      {/* Input */}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
};

export default Index;
