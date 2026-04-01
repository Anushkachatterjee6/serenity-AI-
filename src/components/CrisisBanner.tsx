import { Phone } from "lucide-react";

const CrisisBanner = () => {
  return (
    <div className="bg-crisis-bg border-b border-crisis-border px-4 py-2 flex items-center justify-center gap-2 text-sm text-crisis-text">
      <Phone className="h-3.5 w-3.5" />
      <span>
        If you're in crisis, please call{" "}
        <a href="tel:9152987821" className="font-semibold underline underline-offset-2">
          iCALL: 9152987821
        </a>
      </span>
    </div>
  );
};

export default CrisisBanner;
