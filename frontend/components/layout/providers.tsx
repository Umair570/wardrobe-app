"use client";

import { ThemeProvider } from "@/context/theme-provider";
import { AuthProvider } from "@/context/auth-provider";
import { WardrobeProvider } from "@/context/wardrobe-provider";
import { PageTransition } from "@/components/layout/page-transition";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <WardrobeProvider>
          <PageTransition>{children}</PageTransition>
        </WardrobeProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
