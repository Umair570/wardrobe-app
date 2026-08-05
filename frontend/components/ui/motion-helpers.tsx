import * as React from "react";
import { motion, Variants, AnimatePresence } from "framer-motion";

// Staggered container used across dashboard to cascade children in with a slight delay.
// Using translateY and opacity (transform + opacity) keeps animations GPU accelerated.
const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      when: "beforeChildren",
    },
  },
};

// Fade-up item for a tactile entrance. Includes an exit variant for clean cross-fades.
const fadeUp: Variants = {
  hidden: { opacity: 0, y: 8, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: { type: "spring", stiffness: 320, damping: 28 } },
  exit: { opacity: 0, y: 6, scale: 0.98, transition: { duration: 0.16 } },
};

// FadeIn: simple wrapper for items that should animate in on mount and exit cleanly
export function FadeIn({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.div
      initial="hidden"
      animate="show"
      exit="exit"
      variants={fadeUp}
      className={className}
      style={{ willChange: "transform, opacity" }}
    >
      {children}
    </motion.div>
  );
}

// StaggerContainer: wraps a group of children and staggers their entrance
export function StaggerContainer({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.div
      initial="hidden"
      animate="show"
      variants={staggerContainer}
      className={className}
      style={{ willChange: "transform, opacity" }}
    >
      {children}
    </motion.div>
  );
}

// HoverCard: reusable micro-interaction for cards (lift on hover, subtle press)
// Adds accessibility hooks (role/tabIndex) and ensures motion uses transform only.
export function HoverCard({
  children,
  className,
  as = "div",
  ...rest
}: {
  children: React.ReactNode;
  className?: string;
  as?: keyof React.JSX.IntrinsicElements;
}) {
  const Component: any = (motion as any)[as] || motion.div;

  return (
    <Component
      whileHover={{ y: -3, scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      layout
      className={`group ${className ?? ""}`}
      style={{ willChange: "transform, opacity" }}
      tabIndex={0}
      role="button"
      {...rest}
    >
      {children}
    </Component>
  );
}

export { AnimatePresence };
