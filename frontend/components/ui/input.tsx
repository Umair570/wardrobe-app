import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        "flex h-11 w-full rounded-md border border-ink/12 bg-white px-4 text-sm font-sans text-ink outline-none transition-colors placeholder:text-ink/40 focus-visible:border-forest disabled:cursor-not-allowed disabled:opacity-50 dark:bg-white/5 dark:text-cream dark:border-cream/15 dark:placeholder:text-cream/35",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

export { Input };
