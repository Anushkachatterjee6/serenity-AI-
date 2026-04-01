import { motion } from "framer-motion";
import { Leaf } from "lucide-react";

interface WelcomeScreenProps {
  onStart: (message: string) => void;
}

const prompts = [
  "I've been feeling overwhelmed lately",
  "I need help processing something difficult",
  "I'm looking for ways to manage my anxiety",
  "I just need someone to listen",
];

const WelcomeScreen = ({ onStart }: WelcomeScreenProps) => {
  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="text-center max-w-md"
      >
        <motion.div
          className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-sage-light mb-6"
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        >
          <Leaf className="h-8 w-8 text-primary" />
        </motion.div>

        <h1 className="font-display text-2xl md:text-3xl font-semibold text-foreground mb-3">
          A safe space to talk
        </h1>
        <p className="text-muted-foreground text-sm leading-relaxed mb-8">
          I'm here to listen without judgment. Share what's on your mind, and we'll work through it together at your pace.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {prompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => onStart(prompt)}
              className="text-left text-sm px-4 py-3 rounded-xl bg-card border border-border hover:border-primary/30 hover:bg-sage-light/50 transition-all text-foreground/80"
            >
              {prompt}
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default WelcomeScreen;
