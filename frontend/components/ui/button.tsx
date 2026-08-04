import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-semibold font-sans transition-all disabled:pointer-events-none disabled:opacity-45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2",
  {
    variants: {
      variant: {
        primary: "bg-forest text-cream shadow-[0_6px_20px_rgba(47,79,63,0.28)] hover:-translate-y-0.5 hover:shadow-[0_10px_26px_rgba(47,79,63,0.38)] active:scale-[0.97] active:translate-y-0",
        secondary: "bg-cream-muted text-ink hover:bg-ink/10 dark:bg-white/10 dark:text-cream",
        ghost: "text-ink underline-offset-4 hover:underline dark:text-cream",
        outline: "border border-ink/20 text-ink hover:bg-ink/5 dark:border-cream/30 dark:text-cream",
        destructive: "border border-[#B5502F]/40 text-[#B5502F] bg-transparent hover:bg-[#B5502F]/10",
      },
      size: {
        default: "h-11 px-6",
        sm: "h-9 px-4 text-xs",
        lg: "h-14 px-8 text-base",
        icon: "h-10 w-10 rounded-full",
      },
    },
    defaultVariants: { variant: "primary", size: "default" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size, className }))} {...props} />
  )
);
Button.displayName = "Button";

export { Button, buttonVariants };
