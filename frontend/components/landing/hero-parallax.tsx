"use client";

import * as React from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

const OUTFIT_CARDS = [
  { label: "Evening look", rotate: -8, x: -20, y: 10, z: 1, delay: 0.2, image: "/hero/evening_look.png" },
  { label: "Office edit", rotate: 5, x: 40, y: -30, z: 2, delay: 0.35, image: "/hero/office_edit.png" },
  { label: "Weekend casual", rotate: -3, x: -10, y: 60, z: 3, delay: 0.5, image: "/hero/weekend_casual.png" },
  { label: "Date night", rotate: 10, x: 50, y: 40, z: 4, delay: 0.65, image: "/hero/date_night.png" },
];

export function HeroParallax() {
  const reduced = useReducedMotion();
  const containerRef = React.useRef<HTMLDivElement>(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 80, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 80, damping: 20 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (reduced || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    mouseX.set((e.clientX - cx) / rect.width);
    mouseY.set((e.clientY - cy) / rect.height);
  };

  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative h-[420px] md:h-[520px]"
    >
      {/* Ambient glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-[28px] bg-gradient-to-br from-forest/10 via-transparent to-gold/10 dark:from-forest/20 dark:to-gold/15"
      />

      {OUTFIT_CARDS.map((card, i) => (
        <FloatingCard key={card.label} card={card} index={i} springX={springX} springY={springY} reduced={reduced} />
      ))}

      {/* Chat bubble overlay — "chat → outfit" sequence */}
      <ChatSequence reduced={reduced} />
    </div>
  );
}

function FloatingCard({
  card,
  index,
  springX,
  springY,
  reduced,
}: {
  card: (typeof OUTFIT_CARDS)[0];
  index: number;
  springX: ReturnType<typeof useSpring>;
  springY: ReturnType<typeof useSpring>;
  reduced: boolean;
}) {
  const depth = card.z * 12;
  const parallaxX = useTransform(springX, [-0.5, 0.5], [-depth, depth]);
  const parallaxY = useTransform(springY, [-0.5, 0.5], [-depth * 0.8, depth * 0.8]);

  const sizes = [
    "h-[200px] w-[150px] md:h-[240px] md:w-[175px]",
    "h-[170px] w-[130px] md:h-[200px] md:w-[150px]",
    "h-[160px] w-[120px] md:h-[185px] md:w-[140px]",
    "h-[140px] w-[110px] md:h-[165px] md:w-[125px]",
  ];

  const positions = [
    "left-[5%] top-[8%]",
    "right-[8%] top-[2%]",
    "left-[12%] bottom-[10%]",
    "right-[5%] bottom-[15%]",
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85, rotate: card.rotate - 5 }}
      animate={{ opacity: 1, scale: 1, rotate: card.rotate }}
      transition={{ type: "spring", stiffness: 200, damping: 22, delay: card.delay }}
      style={
        reduced
          ? { zIndex: card.z }
          : { x: parallaxX, y: parallaxY, rotate: card.rotate, zIndex: card.z, willChange: "transform" }
      }
      className={`absolute ${positions[index]} ${sizes[index]}`}
    >
      <motion.div
        animate={reduced ? {} : { y: [0, -8, 0] }}
        transition={{ duration: 4 + index * 0.5, repeat: Infinity, ease: "easeInOut", delay: index * 0.3 }}
        className="relative h-full w-full overflow-hidden rounded-2xl border border-white/60 shadow-2xl dark:border-white/10"
      >
        <img src={card.image} alt={card.label} className="h-full w-full object-cover" />
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/60 to-transparent p-4">
          <p className="font-sans text-sm font-medium text-white">{card.label}</p>
        </div>
      </motion.div>
    </motion.div>
  );
}

function ChatSequence({ reduced }: { reduced: boolean }) {
  const [phase, setPhase] = React.useState<"typing" | "done">("typing");
  const [typed, setTyped] = React.useState("");
  const fullText = "Rooftop dinner tonight?";

  React.useEffect(() => {
    if (reduced) {
      setTyped(fullText);
      setPhase("done");
      return;
    }
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setTyped(fullText.slice(0, i));
      if (i >= fullText.length) {
        clearInterval(interval);
        setTimeout(() => setPhase("done"), 400);
      }
    }, 55);
    return () => clearInterval(interval);
  }, [reduced]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.8, duration: 0.6 }}
      className="absolute bottom-6 left-1/2 z-10 w-[85%] max-w-[280px] -translate-x-1/2"
    >
      <div className="rounded-2xl border border-white/50 bg-white/90 px-4 py-3 shadow-xl backdrop-blur-lg dark:border-white/10 dark:bg-ink/90">
        <p className="font-sans text-[13px] text-ink dark:text-cream">
          {typed}
          {phase === "typing" && (
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.6, repeat: Infinity }}
              className="ml-0.5 inline-block h-3.5 w-0.5 bg-forest align-middle dark:bg-[#8fbfa4]"
            />
          )}
        </p>
      </div>
      {phase === "done" && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute -top-4 right-0 animate-float-y rounded-full bg-forest px-3.5 py-1.5 font-sans text-[11px] font-semibold text-cream shadow-lg motion-reduce:animate-none dark:bg-[#8fbfa4] dark:text-ink"
        >
          ✦ 3 looks generated
        </motion.div>
      )}
    </motion.div>
  );
}
