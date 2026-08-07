"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { AppNav } from "@/components/layout/app-nav";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";
import { useAuth } from "@/context/auth-provider";
import { getWardrobeStats } from "@/lib/api/wardrobe";
import { getProfile, uploadBodyPhoto, deleteBodyPhoto } from "@/lib/api/profile";
import { Upload, Trash2 } from "lucide-react";

const PREFS = ["Minimal", "Tailored", "Earth tones", "Relaxed"];

export default function ProfilePage() {
  const { user, signOut, loading: authLoading } = useAuth();
  const router = useRouter();
  const [selected, setSelected] = React.useState<Record<string, boolean>>({
    Minimal: true,
    "Earth tones": true,
  });
  const [showAdvanced, setShowAdvanced] = React.useState(false);
  const [stats, setStats] = React.useState({ itemsInCloset: 0, looksSaved: 0, stylistQueries: 0 });
  const [statsLoading, setStatsLoading] = React.useState(true);
  const [bodyPhotoUrl, setBodyPhotoUrl] = React.useState<string | null>(null);
  const [profileName, setProfileName] = React.useState<string | null>(null);
  const [uploadingBody, setUploadingBody] = React.useState(false);

  React.useEffect(() => {
    Promise.all([getWardrobeStats(), getProfile()])
      .then(([statsData, profileData]) => {
        setStats({
          itemsInCloset: statsData.items_in_closet,
          looksSaved: statsData.looks_saved,
          stylistQueries: statsData.stylist_queries,
        });
        if (profileData.body_photo_url) {
          setBodyPhotoUrl(profileData.body_photo_url);
        }
        if (profileData.display_name) {
          setProfileName(profileData.display_name);
        }
      })
      .catch(() => {})
      .finally(() => setStatsLoading(false));
  }, []);

  React.useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/auth");
    }
  }, [user, authLoading, router]);

  async function handleBodyUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingBody(true);
    try {
      const res = await uploadBodyPhoto(file);
      if (res.body_photo_url) setBodyPhotoUrl(res.body_photo_url);
    } catch (err) {
      console.error(err);
    } finally {
      setUploadingBody(false);
    }
  }

  async function handleDeleteBodyPhoto() {
    setUploadingBody(true);
    try {
      await deleteBodyPhoto();
      setBodyPhotoUrl(null);
    } catch (err) {
      console.error(err);
    } finally {
      setUploadingBody(false);
    }
  }

  async function handleSignOut() {
    await signOut();
    router.push("/auth");
  }

  const displayName = profileName || user?.user_metadata?.display_name || user?.email?.split("@")[0] || "User";
  const email = user?.email || "";
  const initials = displayName.charAt(0).toUpperCase();

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
            <Avatar fallback={initials} size={76} className="text-2xl" />
            <div className="flex-1">
              {authLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-6 w-40" />
                  <Skeleton className="h-4 w-48" />
                </div>
              ) : (
                <>
                  <h2 className="font-heading text-2xl font-semibold text-ink dark:text-cream">{displayName}</h2>
                  <p className="mt-1 font-sans text-[13.5px] text-ink/55 dark:text-cream/55">{email}</p>
                </>
              )}
            </div>
          </div>
        </section>

        {/* Stats section */}
        <section className="mt-5">
          <p className="mb-3 font-mono text-[10.5px] tracking-wide text-ink/50 dark:text-cream/50">YOUR STATS</p>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "ITEMS IN CLOSET", value: stats.itemsInCloset },
              { label: "LOOKS SAVED", value: stats.looksSaved },
              { label: "STYLIST QUERIES", value: stats.stylistQueries },
            ].map((stat) => (
              <motion.div
                key={stat.label}
                whileHover={{ y: -2 }}
                className="rounded-md bg-card p-5 text-center shadow-[0_4px_16px_rgba(30,30,30,0.06)]"
              >
                {statsLoading ? (
                  <Skeleton className="mx-auto h-8 w-12" />
                ) : (
                  <p className="font-heading text-[28px] font-semibold text-forest dark:text-[#8fbfa4]">{stat.value}</p>
                )}
                <p className="mt-1.5 font-mono text-[10.5px] tracking-wide text-ink/50 dark:text-cream/50">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Body Photo section */}
        <section className="mt-8">
          <p className="mb-3 font-mono text-[10.5px] tracking-wide text-ink/50 dark:text-cream/50">VIRTUAL TRY-ON MODEL</p>
          <div className="rounded-lg bg-card p-6 shadow-[0_4px_16px_rgba(30,30,30,0.06)]">
            <div className="flex flex-col md:flex-row gap-6 items-center">
              <div className="relative h-48 w-36 shrink-0 overflow-hidden rounded-md bg-cream-muted dark:bg-white/5 border border-ink/10 dark:border-cream/10">
                {bodyPhotoUrl ? (
                  <img src={bodyPhotoUrl} alt="Body photo" className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full flex-col items-center justify-center text-ink/30 dark:text-cream/30">
                    <span className="font-mono text-xs">No image</span>
                  </div>
                )}
                {uploadingBody && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm">
                    <span className="font-mono text-[10px] text-white">UPDATING...</span>
                  </div>
                )}
              </div>
              <div className="flex-1 space-y-3 text-center md:text-left">
                <p className="font-sans text-[13.5px] text-ink/70 dark:text-cream/70">
                  Upload a full body photo to use as your default model for AI virtual try-on. Use a well-lit photo with a plain background for best results.
                </p>
                <div className="flex flex-wrap items-center gap-3 justify-center md:justify-start">
                  <Button variant="secondary" size="sm" className="relative overflow-hidden" disabled={uploadingBody}>
                    <Upload className="mr-2 h-3.5 w-3.5" />
                    Upload photo
                    <input
                      type="file"
                      accept="image/jpeg, image/png, image/webp"
                      className="absolute inset-0 cursor-pointer opacity-0"
                      onChange={handleBodyUpload}
                    />
                  </Button>
                  {bodyPhotoUrl && (
                    <Button variant="outline" size="sm" onClick={handleDeleteBodyPhoto} disabled={uploadingBody}>
                      <Trash2 className="mr-2 h-3.5 w-3.5" />
                      Remove
                    </Button>
                  )}
                </div>
              </div>
            </div>
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

        <Button variant="destructive" className="mt-10" onClick={handleSignOut}>
          Sign out
        </Button>
      </div>
    </div>
  );
}
