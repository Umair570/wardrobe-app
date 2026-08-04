import * as React from "react";
import { cn } from "@/lib/utils";

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  fallback: string;
  src?: string;
  size?: number;
}

function Avatar({ fallback, src, size = 40, className, ...props }: AvatarProps) {
  return (
    <div
      className={cn(
        "relative flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-forest font-sans font-bold text-cream",
        className
      )}
      style={{ width: size, height: size, fontSize: size * 0.36 }}
      {...props}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt={fallback} className="h-full w-full object-cover" />
      ) : (
        fallback
      )}
    </div>
  );
}

export { Avatar };
