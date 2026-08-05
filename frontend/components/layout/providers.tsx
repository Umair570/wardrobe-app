"use client";

import { ThemeProvider } from "@/context/theme-provider";
import { WardrobeProvider } from "@/context/wardrobe-provider";
import { PageTransition } from "@/components/layout/page-transition";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <WardrobeProvider>
        <PageTransition>{children}</PageTransition>
      </WardrobeProvider>
    </ThemeProvider>
  );
}
