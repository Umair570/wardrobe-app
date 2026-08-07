import { Link, useRouterState } from "@tanstack/react-router";
import { LayoutDashboard, Shirt, Sparkles, LogOut, MessageSquare, Wand2, User } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { ProfileDrawer } from "./ProfileDrawer";
import { useProfile } from "@/hooks/useProfile";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/wardrobe", label: "Wardrobe", icon: Shirt },
  { to: "/stylist", label: "AI Stylist", icon: MessageSquare },
  { to: "/tryon", label: "Try-On", icon: Wand2 },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [profileOpen, setProfileOpen] = useState(false);
  const { data: profile } = useProfile();
  const displayName = profile?.display_name || profile?.email?.split("@")[0] || "User";
  const initials = displayName.slice(0, 2).toUpperCase();

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[248px] flex-col justify-between border-r border-border bg-ink px-6 py-8 md:flex">
        <div>
          <Link to="/" className="block text-2xl uppercase text-beige display-xl">
            Atelier
          </Link>
          <p className="mt-2 text-[0.6rem] font-bold uppercase tracking-[0.32em] text-beige/40">
            AI Wardrobe
          </p>
          <nav className="mt-12 space-y-1.5">
            {nav.map(({ to, label, icon: Icon }) => {
              const active = pathname === to;
              return (
                <Link
                  key={to}
                  to={to}
                  className={cn(
                    "flex items-center gap-3 rounded-full px-4 py-3 text-xs font-bold uppercase tracking-[0.16em] transition-all duration-300",
                    active
                      ? "bg-beige text-ink"
                      : "text-beige/60 hover:bg-beige/10 hover:text-beige",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Bottom: Profile + Sign out */}
        <div className="space-y-2">
          {/* Profile avatar */}
          <button
            id="profile-button"
            onClick={() => setProfileOpen(true)}
            className="flex w-full items-center gap-3 rounded-full px-4 py-3 text-left text-xs font-bold uppercase tracking-[0.16em] text-beige/60 transition-all hover:bg-beige/10 hover:text-beige"
          >
            <div className="flex h-8 w-8 shrink-0 overflow-hidden items-center justify-center rounded-full bg-beige/20 text-[0.55rem] font-black text-beige">
              {profile?.body_photo_url ? (
                <img src={profile.body_photo_url} alt="Profile" className="h-full w-full object-cover" />
              ) : (
                initials
              )}
            </div>
            <span className="truncate">{displayName}</span>
          </button>
          <Link
            to="/auth"
            className="flex items-center gap-3 rounded-full px-4 py-3 text-xs font-bold uppercase tracking-[0.16em] text-beige/50 transition-colors hover:text-gold"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </Link>
        </div>
      </aside>

      <main className="pb-28 md:pb-0 md:pl-[248px]">{children}</main>

      {/* Mobile bottom nav — show 4 most important */}
      <nav className="glass fixed inset-x-4 bottom-4 z-40 flex items-center justify-around rounded-full px-2 py-2 shadow-luxe md:hidden">
        {nav.slice(0, 4).map(({ to, label, icon: Icon }) => {
          const active = pathname === to;
          return (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex flex-1 flex-col items-center gap-1 rounded-full py-2 text-[0.6rem] font-bold uppercase tracking-[0.14em] transition-colors",
                active ? "bg-ink text-beige" : "text-muted-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
        {/* Profile button in mobile nav */}
        <button
          onClick={() => setProfileOpen(true)}
          className="flex flex-1 flex-col items-center gap-1 rounded-full py-2 text-[0.6rem] font-bold uppercase tracking-[0.14em] text-muted-foreground"
        >
          <User className="h-4 w-4" />
          Me
        </button>
      </nav>

      <ProfileDrawer open={profileOpen} onClose={() => setProfileOpen(false)} />
    </div>
  );
}

export function PageHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <header className="animate-rise-in">
      <p className="text-[0.62rem] font-bold uppercase tracking-[0.32em] text-muted-foreground">
        {subtitle}
      </p>
      <h1 className="mt-3 text-4xl uppercase sm:text-5xl display-xl">{title}</h1>
    </header>
  );
}