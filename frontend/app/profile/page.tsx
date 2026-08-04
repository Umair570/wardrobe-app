"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppNav } from "@/components/layout/app-nav";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";
import type { UserProfile } from "@/types";

const PREFS = ["Minimal", "Tailored", "Earth tones", "Relaxed"];

const PROFILE: UserProfile = {
  id: "1",
  name: "Maya Chen",
  email: "maya@wardrobe.ai",
  stats: { itemsInCloset: 24, looksSaved: 8, stylistQueries: 37 },
  preferences: ["Minimal", "Earth tones"],
};

export default function ProfilePage() {
  const [selected, setSelected] = React.useState<Record<string, boolean>>(
    Object.fromEntries(PROFILE.preferences.map((p) => [p, true]))
  );
  const [showAdvanced, setShowAdvanced] = React.useState(false);

  return (
    <div className="min-h-screen bg-cream dark:bg-[#161611]">
      <AppNav />
      <div className="mx-auto max-w-2xl px-6 pb-24 pt-11 md:px-12">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <span className="font-mono text-[11.5px] font-semibold tracking-wide text-gold">YOUR ACCOUNT</span>
          <h1 className="mb-8 mt-2 font-heading text-[clamp(30px,3.6vw,44px)] font-semibold text-ink dark:text-cream">
            Profile
          </h1>
        </motion.div>

        {/* Profile header section */}
        <section className="rounded-lg bg-card p-6 shadow-[0_4px_16px_rgba(30,30,30,0.06)]">
          <div className="flex items-center gap-5">
            <Avatar fallback="M" size={76} className="text-2xl" />
            <div className="flex-1">
              <h2 className="font-heading text-2xl font-semibold text-ink dark:text-cream">{PROFILE.name}</h2>
              <p className="mt-1 font-sans text-[13.5px] text-ink/55 dark:text-cream/55">{PROFILE.email}</p>
            </div>
            <Button variant="secondary" size="sm">
              Edit profile
            </Button>
          </div>
        </section>

        {/* Stats section */}
        <section className="mt-5">
          <p className="mb-3 font-mono text-[10.5px] tracking-wide text-ink/50 dark:text-cream/50">YOUR STATS</p>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "ITEMS IN CLOSET", value: PROFILE.stats.itemsInCloset },
              { label: "LOOKS SAVED", value: PROFILE.stats.looksSaved },
              { label: "STYLIST QUERIES", value: PROFILE.stats.stylistQueries },
            ].map((stat) => (
              <motion.div
                key={stat.label}
                whileHover={{ y: -2 }}
                className="rounded-md bg-card p-5 text-center shadow-[0_4px_16px_rgba(30,30,30,0.06)]"
              >
                <p className="font-heading text-[28px] font-semibold text-forest dark:text-[#8fbfa4]">{stat.value}</p>
                <p className="mt-1.5 font-mono text-[10.5px] tracking-wide text-ink/50 dark:text-cream/50">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Style preferences */}
        <section className="mt-8">
          <p className="mb-3 font-mono text-[10.5px] tracking-wide text-ink/50 dark:text-cream/50">STYLE PREFERENCES</p>
          <div className="flex flex-wrap gap-2.5">
            {PREFS.map((pref) => (
              <motion.button
                key={pref}
                whileTap={{ scale: 0.97 }}
                onClick={() => setSelected((s) => ({ ...s, [pref]: !s[pref] }))}
                className={cn(
                  "rounded-full px-[18px] py-2.5 font-sans text-[13px] font-semibold transition-colors",
                  selected[pref] ? "bg-forest text-cream dark:bg-[#3d6b54]" : "bg-cream-muted text-ink dark:bg-white/10 dark:text-cream"
                )}
              >
                {pref}
              </motion.button>
            ))}
          </div>
        </section>

        {/* Advanced settings — collapsed */}
        <section className="mt-8">
          <button
            onClick={() => setShowAdvanced((s) => !s)}
            className="flex w-full items-center justify-between rounded-lg border border-ink/8 bg-card/50 px-4 py-3 font-sans text-sm text-ink/70 dark:border-cream/8 dark:text-cream/70"
          >
            Advanced settings
            <ChevronDown className={cn("h-4 w-4 transition-transform", showAdvanced && "rotate-180")} />
          </button>
          <AnimatePresence>
            {showAdvanced && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden"
              >
                <div className="mt-3 space-y-3 rounded-lg border border-ink/8 bg-card/30 p-4 dark:border-cream/8">
                  {["Export wardrobe data", "Notification preferences", "Connected accounts", "Delete account"].map((item) => (
                    <button
                      key={item}
                      className="block w-full text-left font-sans text-sm text-ink/60 hover:text-ink dark:text-cream/60 dark:hover:text-cream"
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </section>

        <Button variant="destructive" className="mt-10">
          Sign out
        </Button>
      </div>
    </div>
  );
}
