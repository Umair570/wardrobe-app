"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { useAuth } from "@/context/auth-provider";
import { LogOut, User as UserIcon } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

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
  const { user, signOut } = useAuth();
  const router = useRouter();
  const [dropdownOpen, setDropdownOpen] = React.useState(false);

  const rawName = user?.user_metadata?.display_name || user?.email?.split("@")[0] || "U";
  const displayName = rawName.charAt(0).toUpperCase() + rawName.slice(1);
  const initial = displayName.charAt(0).toUpperCase();

  const handleSignOut = async () => {
    await signOut();
    router.push("/auth");
  };

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

      <div className="flex items-center gap-3 relative">
        <ThemeToggle />
        <button
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="relative rounded-full focus:outline-none focus:ring-2 focus:ring-gold focus:ring-offset-2 dark:focus:ring-offset-[#161611]"
        >
          <Avatar fallback={initial} size={34} />
        </button>

        <AnimatePresence>
          {dropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setDropdownOpen(false)}
              />
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-12 z-50 w-56 rounded-xl border border-ink/10 bg-cream p-2 shadow-lg dark:border-cream/10 dark:bg-[#161611]"
              >
                <div className="px-3 py-2 mb-2 border-b border-ink/5 dark:border-cream/5">
                  <p className="font-sans text-sm font-semibold text-ink dark:text-cream truncate">
                    {displayName}
                  </p>
                  <p className="font-sans text-xs text-ink/60 dark:text-cream/60 truncate">
                    {user?.email}
                  </p>
                </div>
                <div className="flex flex-col gap-1">
                  <Link
                    href="/profile"
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink/80 transition-colors hover:bg-ink/5 hover:text-ink dark:text-cream/80 dark:hover:bg-cream/5 dark:hover:text-cream"
                  >
                    <UserIcon className="h-4 w-4" />
                    Profile Details
                  </Link>
                  <button
                    onClick={handleSignOut}
                    className="flex items-center gap-2 w-full text-left rounded-lg px-3 py-2 text-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10"
                  >
                    <LogOut className="h-4 w-4" />
                    Log out
                  </button>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    </nav>
  );
}
