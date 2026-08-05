import * as React from "react";
import { ImagePlaceholder } from "@/components/ui/image-placeholder";
import { HoverCard } from "@/components/ui/motion-helpers";
import { Sparkles } from "lucide-react";
import type { OutfitRecommendation } from "@/types";

// Polished recommendation card.
export function RecommendationCard({ rec }: { rec: OutfitRecommendation }) {
  return (
    <HoverCard className="flex items-center gap-4 rounded-2xl bg-white/6 backdrop-blur-md border border-white/8 p-4 shadow-[0_10px_30px_rgba(0,0,0,0.06)]">
      <div className="h-14 w-14 flex-shrink-0 overflow-hidden rounded-xl ring-1 ring-white/6">
        <ImagePlaceholder />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-3">
          <p className="truncate text-sm font-semibold text-ink dark:text-cream">{rec.title}</p>

          <div
            title={`${rec.match}% match`}
            className="flex items-center gap-1 rounded-full bg-gradient-to-br from-gold/10 to-gold/6 px-2 py-0.5 text-xs font-semibold text-gold shadow-[0_6px_20px_rgba(201,164,92,0.06)]"
          >
            <Sparkles size={12} />
            <span>{rec.match}%</span>
          </div>
        </div>

        <div className="mt-2 text-xs text-ink/50 dark:text-cream/50 truncate">{rec.hint ?? "Styled for a warm evening"}</div>
      </div>
    </HoverCard>
  );
}
