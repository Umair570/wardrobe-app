import * as React from "react";
import { cn } from "@/lib/utils";

function Separator({ className, ...props }: React.HTMLAttributes<HTMLHRElement>) {
  return (
    <hr
      className={cn("border-0 border-t border-ink/8 dark:border-cream/10", className)}
      {...props}
    />
  );
}

export { Separator };
