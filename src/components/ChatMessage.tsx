import ReactMarkdown from "react-markdown";
import { motion } from "framer-motion";

type Message = {
  role: "user" | "assistant";
  content: string;
};

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

const ChatMessage = ({ message, isStreaming }: ChatMessageProps) => {
  const isUser = message.role === "user";

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
          <div className="prose prose-sm max-w-none text-ai-bubble-foreground prose-p:leading-relaxed prose-p:mb-2 last:prose-p:mb-0">
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {isStreaming && (
              <span className="inline-block w-1.5 h-4 bg-primary/50 rounded-full animate-breathe ml-0.5 align-middle" />
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default ChatMessage;
