"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/layout/theme-toggle";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/wardrobe", label: "Wardrobe" },
  { href: "/upload", label: "Upload" },
  { href: "/stylist", label: "AI Stylist" },
  { href: "/studio", label: "Studio" },
  { href: "/try-on", label: "Try-On" },
  { href: "/saved", label: "Saved" },
  { href: "/profile", label: "Profile" },
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-20 flex flex-wrap items-center justify-between gap-3 border-b border-ink/10 bg-cream/95 px-6 py-4 backdrop-blur dark:border-cream/10 dark:bg-[#161611]/95 md:px-10">
      <Link href="/" className="flex items-center gap-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-ink font-heading text-base font-semibold text-cream dark:bg-cream dark:text-ink">
          W
        </span>
        <span className="font-sans text-[15px] font-bold text-ink dark:text-cream">Tailored for you</span>
      </Link>

      <div className="flex flex-wrap items-center gap-5">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "border-b-2 border-transparent pb-1 font-sans text-[13.5px] transition-colors",
                active
                  ? "border-gold font-bold text-ink dark:text-cream"
                  : "font-medium text-ink/55 hover:text-ink dark:text-cream/55 dark:hover:text-cream"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </div>

      <div className="flex items-center gap-3">
        <ThemeToggle />
        <Avatar fallback="M" size={34} />
      </div>
    </nav>
  );
}
