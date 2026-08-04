import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

export function Surface({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("glass rounded-3xl shadow-soft", className)} {...rest} />;
}

export function Eyebrow({ className, ...rest }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 text-[0.65rem] font-bold uppercase tracking-[0.32em] text-muted-foreground",
        className,
      )}
      {...rest}
    />
  );
}