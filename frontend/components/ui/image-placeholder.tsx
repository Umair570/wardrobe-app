import { cn } from "@/lib/utils";
import { ImageIcon } from "lucide-react";

interface ImagePlaceholderProps {
  label?: string;
  className?: string;
  rounded?: string;
}

export function ImagePlaceholder({ label, className, rounded = "rounded-md" }: ImagePlaceholderProps) {
  return (
    <div
      className={cn(
        "relative flex h-full w-full items-center justify-center overflow-hidden",
        "bg-gradient-to-br from-cream-muted via-cream to-cream-muted/80",
        "dark:from-white/[0.06] dark:via-white/[0.04] dark:to-white/[0.08]",
        "text-ink/35 dark:text-cream/25",
        rounded,
        className
      )}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/50 to-transparent dark:via-white/10 motion-reduce:animate-none"
      />
      <div className="relative flex flex-col items-center gap-1.5 px-2 text-center">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-ink/[0.04] dark:bg-white/[0.06]">
          <ImageIcon className="h-4 w-4 opacity-60" />
        </div>
        {label ? <span className="font-sans text-[10px] leading-tight opacity-70">{label}</span> : null}
      </div>
    </div>
  );
}
