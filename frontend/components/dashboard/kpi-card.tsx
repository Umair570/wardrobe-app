import * as React from "react";
import { TrendingUp, Archive } from "lucide-react";
import { HoverCard } from "@/components/ui/motion-helpers";

type KPIProps = {
  title: string;
  value: string | number;
  delta?: string; // e.g. +3.2%
  icon?: React.ReactNode;
};

// Small decorative sparkline used for the KPI visual. It's decorative only and keeps animation GPU-friendly.
function MiniSparkline({ color = "#C9A45C" }: { color?: string }) {
  return (
    <svg width="64" height="24" viewBox="0 0 64 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="ml-2">
      <defs>
        <linearGradient id="g1" x1="0" x2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0.06" />
        </linearGradient>
      </defs>
      <path d="M2 18 L12 12 L22 14 L32 8 L42 10 L52 6 L62 10" stroke={color} strokeWidth="1.6" strokeOpacity="0.95" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="0" y="0" width="64" height="24" fill="url(#g1)" />
    </svg>
  );
}

export function KPICard({ title, value, delta, icon }: KPIProps) {
  return (
    <HoverCard className={`rounded-2xl bg-white/6 backdrop-blur-md border border-white/8 p-4 shadow-[0_6px_30px_rgba(0,0,0,0.08)]`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-medium uppercase tracking-wide text-ink/50 dark:text-cream/50">{title}</div>

          <div className="mt-1 flex items-center gap-3">
            <div className="text-2xl font-heading font-semibold text-ink dark:text-cream">{value}</div>

            {delta ? (
              <div className="flex items-center gap-1 rounded-full bg-green-700/12 px-2 py-0.5 text-sm font-medium text-green-400 shadow-[0_6px_18px_rgba(16,185,129,0.06)]">
                <TrendingUp size={14} />
                <span>{delta}</span>
              </div>
            ) : null}

            {/* Decorative sparkline helps convey trend at a glance */}
            <MiniSparkline color={delta && delta.includes("-") ? "#EF4444" : "#10B981"} />
          </div>
        </div>

        <div className="shrink-0 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-white/6 to-white/3 ring-1 ring-white/4">
          {icon ?? <Archive size={18} className="text-ink/70 dark:text-cream/70" />}
        </div>
      </div>
    </HoverCard>
  );
}
