import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ink" | "outline" | "ghost" | "glow";
type Size = "sm" | "md" | "lg";

const variants: Record<Variant, string> = {
  primary:
    "bg-forest text-primary-foreground hover:bg-forest-deep shadow-soft",
  ink: "bg-ink text-beige hover:bg-forest-deep",
  outline:
    "border border-ink/25 text-foreground hover:border-forest hover:text-forest",
  ghost: "text-foreground/70 hover:text-forest hover:bg-secondary/60",
  glow: "bg-ink text-gold animate-glow hover:bg-forest-deep",
};

const sizes: Record<Size, string> = {
  sm: "h-9 px-4 text-xs",
  md: "h-11 px-6 text-sm",
  lg: "h-14 px-8 text-sm",
};

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
}

export function Button({ variant = "primary", size = "md", className, children, ...rest }: Props) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-full font-semibold uppercase tracking-[0.14em] transition-all duration-300 active:scale-[0.97] disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}