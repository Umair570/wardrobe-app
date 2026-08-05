import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full font-mono font-semibold tracking-wide",
  {
    variants: {
      variant: {
        default: "bg-cream-muted text-ink dark:bg-white/10 dark:text-cream",
        accent: "bg-forest/10 text-forest dark:bg-forest/20 dark:text-[#8fbfa4]",
        gold: "bg-gold-soft text-[#9c7a3a] dark:text-gold",
      },
      size: {
        default: "text-[10px] px-2.5 py-1",
        sm: "text-[9px] px-2 py-0.5",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, size, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, size, className }))} {...props} />;
}

export { Badge, badgeVariants };
