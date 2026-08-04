"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export function SiteNav() {
  return (
    <nav className="sticky top-0 z-20 flex items-center justify-between border-b border-ink/10 bg-cream/70 px-6 py-5 backdrop-blur-md dark:border-cream/10 dark:bg-[#161611]/70 md:px-12">
      <span className="font-heading text-2xl italic font-semibold text-ink dark:text-cream">
        Wardrobe.AI
      </span>
      <div className="flex items-center gap-8">
        <Link href="#how" className="hidden font-sans text-sm text-ink dark:text-cream md:inline">
          How it works
        </Link>
        <Link href="#features" className="hidden font-sans text-sm text-ink dark:text-cream md:inline">
          Features
        </Link>
        <Link href="/auth" className="hidden font-sans text-sm text-ink dark:text-cream md:inline">
          Log in
        </Link>
        <ThemeToggle />
        <Link href="/auth">
          <Button>Get Started</Button>
        </Link>
      </div>
    </nav>
  );
}
