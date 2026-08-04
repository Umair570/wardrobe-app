"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { ImagePlaceholder } from "@/components/ui/image-placeholder";
import { cn } from "@/lib/utils";

export function BeforeAfterSlider() {
  const [position, setPosition] = React.useState(50);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const dragging = React.useRef(false);

  const updatePosition = (clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const pct = Math.max(8, Math.min(92, ((clientX - rect.left) / rect.width) * 100));
    setPosition(pct);
  };

  return (
    <div
      ref={containerRef}
      className="relative mt-4 aspect-[4/3] cursor-ew-resize select-none overflow-hidden rounded-md"
      onPointerDown={(e) => {
        dragging.current = true;
        updatePosition(e.clientX);
        (e.target as HTMLElement).setPointerCapture(e.pointerId);
      }}
      onPointerMove={(e) => dragging.current && updatePosition(e.clientX)}
      onPointerUp={() => (dragging.current = false)}
    >
      <div className="absolute inset-0">
        <ImagePlaceholder label="Original" rounded="rounded-none" />
      </div>
      <div className="absolute inset-0 overflow-hidden" style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}>
        <ImagePlaceholder label="Styled on you" rounded="rounded-none" />
      </div>
      <div
        className="absolute inset-y-0 z-10 w-0.5 bg-gold shadow-[0_0_8px_rgba(201,164,92,0.6)]"
        style={{ left: `${position}%` }}
      >
        <div className="absolute left-1/2 top-1/2 flex h-7 w-7 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-gold shadow-lg">
          <span className="font-mono text-[10px] font-bold text-ink">↔</span>
        </div>
      </div>
      <div className="pointer-events-none absolute bottom-2 left-2 rounded-full bg-black/40 px-2 py-0.5 font-mono text-[9px] text-white backdrop-blur-sm">
        BEFORE
      </div>
      <div className="pointer-events-none absolute bottom-2 right-2 rounded-full bg-black/40 px-2 py-0.5 font-mono text-[9px] text-white backdrop-blur-sm">
        AFTER
      </div>
    </div>
  );
}

interface FeatureCardProps {
  title: string;
  copy: string;
  index: number;
  rich?: boolean;
}

export function FeatureCard({ title, copy, index, rich }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 22, scale: 0.97 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true }}
      whileHover={{ y: -6, scale: rich ? 1.01 : 1.02 }}
      transition={{ type: "spring", stiffness: 280, damping: 24, delay: index * 0.1 }}
      className={cn(
        "rounded-lg bg-card p-8 shadow-[0_4px_20px_rgba(30,30,30,0.06)] transition-shadow hover:shadow-[0_12px_40px_rgba(30,30,30,0.1)] dark:hover:shadow-[0_12px_40px_rgba(0,0,0,0.3)]",
        rich && "md:row-span-1 ring-1 ring-gold/20"
      )}
    >
      <h3 className="mb-2 font-sans text-lg font-bold text-ink dark:text-cream">{title}</h3>
      <p className="font-sans text-[14.5px] leading-relaxed text-ink/62 dark:text-cream/60">{copy}</p>
      {rich && <BeforeAfterSlider />}
    </motion.div>
  );
}
