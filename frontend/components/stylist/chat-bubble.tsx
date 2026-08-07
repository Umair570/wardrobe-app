import { motion } from "framer-motion";
import type { ChatMessage } from "@/types";
import { ImagePlaceholder } from "@/components/ui/image-placeholder";
import { cn } from "@/lib/utils";
import { Sparkles } from "lucide-react";
import { useWardrobe } from "@/hooks/use-wardrobe";

export function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const { items } = useWardrobe();

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 28 }}
      className={cn("flex", isUser ? "justify-end" : "justify-start")}
    >
      {isUser ? (
        <div className="max-w-[70%] rounded-2xl rounded-br-md bg-forest px-[18px] py-3.5 font-sans text-[14.5px] text-cream dark:bg-[#3d6b54]">
          {message.text}
        </div>
      ) : (
        <div className="max-w-[85%] rounded-2xl rounded-bl-md bg-card p-[18px] shadow-[0_4px_16px_rgba(30,30,30,0.06)] dark:shadow-[0_4px_16px_rgba(0,0,0,0.2)]">
          <p className="mb-3 font-sans text-[14.5px] leading-relaxed text-ink dark:text-cream">{message.text}</p>
          {message.outfits && message.outfits.length > 0 ? (
            <div className="mt-4 flex flex-col gap-4">
              {message.outfits.map((outfit, idx) => (
                <div key={idx} className="overflow-hidden rounded-xl border border-ink/5 bg-cream-muted/50 p-4 dark:border-cream/5 dark:bg-white/[0.04]">
                  <div className="mb-3">
                    <h4 className="font-sans text-sm font-semibold text-ink dark:text-cream">{outfit.title}</h4>
                    <p className="mt-1 font-sans text-xs text-ink/70 dark:text-cream/70">{outfit.rationale}</p>
                  </div>
                  <div className="flex gap-2">
                    {(["top_id", "outerwear_id", "bottom_id", "shoes_id"] as const).map((slotKey) => {
                      const itemId = outfit[slotKey];
                      if (!itemId) return null;
                      const item = items.find((i) => i.id === itemId);
                      const displaySlot = slotKey.replace("_id", "");
                      
                      return (
                        <div key={slotKey} className="flex-1 max-w-[80px]">
                          <div className="aspect-square overflow-hidden rounded-md bg-white/5 border border-ink/5 dark:border-white/5">
                            {item?.imageUrl ? (
                              <img src={item.imageUrl} alt={item.name} className="h-full w-full object-cover" />
                            ) : (
                              <ImagePlaceholder label={displaySlot} />
                            )}
                          </div>
                          <p className="mt-1.5 text-center font-mono text-[9px] uppercase tracking-wide text-ink/50 dark:text-cream/50">
                            {displaySlot}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          ) : message.look ? (
            <div className="mt-4 overflow-hidden rounded-xl border border-ink/5 bg-cream-muted/50 p-3 dark:border-cream/5 dark:bg-white/[0.04]">
              <div className="mb-2 flex items-center gap-1.5">
                <Sparkles className="h-3 w-3 text-gold" />
                <span className="font-mono text-[10px] tracking-wide text-gold">SUGGESTED LOOK</span>
              </div>
              <div className="flex gap-2">
                {(["top", "bottom", "shoes"] as const).map((slot) => {
                  const itemId = message.look![slot];
                  if (!itemId) return null;
                  const item = items.find((i) => i.id === itemId);
                  return (
                    <div key={slot} className="flex-1">
                      <div className="aspect-square overflow-hidden rounded-md bg-white/5">
                        {item?.imageUrl ? (
                          <img src={item.imageUrl} alt={item.name} className="h-full w-full object-cover" />
                        ) : (
                          <ImagePlaceholder label={slot} />
                        )}
                      </div>
                      <p className="mt-1 text-center font-mono text-[9px] uppercase tracking-wide text-ink/45 dark:text-cream/45">
                        {slot}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </motion.div>
  );
}
