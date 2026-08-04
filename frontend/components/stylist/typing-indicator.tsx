"use client";

import { motion } from "framer-motion";

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex w-fit items-center gap-3 rounded-2xl bg-card px-[18px] py-3.5 shadow-[0_4px_16px_rgba(30,30,30,0.06)] dark:shadow-[0_4px_16px_rgba(0,0,0,0.2)]"
    >
      <span className="font-sans text-xs text-ink/45 dark:text-cream/45">Styling</span>
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="h-2 w-2 rounded-full bg-forest dark:bg-[#8fbfa4]"
            animate={{ scale: [1, 1.4, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15, ease: "easeInOut" }}
          />
        ))}
      </div>
    </motion.div>
  );
}
