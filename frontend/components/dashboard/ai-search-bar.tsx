"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

interface AiSearchBarProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  placeholder?: string;
}

export function AiSearchBar({ value, onChange, onSubmit, placeholder }: AiSearchBarProps) {
  const reduced = useReducedMotion();

  return (
    <motion.form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      whileFocus={{ scale: 1.005 }}
      className="group relative flex items-center gap-3.5 rounded-full border border-ink/10 bg-card px-6 py-4 shadow-[0_8px_32px_rgba(30,30,30,0.1)] transition-shadow focus-within:shadow-[0_0_0_3px_rgba(47,79,63,0.18),0_12px_40px_rgba(47,79,63,0.12)] dark:border-cream/10 dark:focus-within:shadow-[0_0_0_3px_rgba(143,191,164,0.2),0_12px_40px_rgba(0,0,0,0.3)]"
    >
      {/* Animated gradient border glow */}
      {!reduced && (
        <div
          aria-hidden
          className="pointer-events-none absolute -inset-px animate-glow-pulse rounded-full bg-gradient-to-r from-forest/30 via-gold/20 to-forest/30 opacity-0 transition-opacity group-focus-within:opacity-100 motion-reduce:animate-none"
        />
      )}
      <div className="relative flex w-full items-center gap-3.5">
        <Sparkles className="h-[18px] w-[18px] shrink-0 text-gold" />
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder ?? "What would you like to wear today?"}
          className="flex-1 bg-transparent font-sans text-[16px] text-ink outline-none placeholder:text-ink/45 dark:text-cream dark:placeholder:text-cream/40"
        />
        <Button type="submit" size="sm" className="shrink-0">
          Ask
        </Button>
      </div>
    </motion.form>
  );
}
