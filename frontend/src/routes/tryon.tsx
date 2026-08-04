import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "motion/react";
import { useState, useRef } from "react";
import { ArrowLeft, Upload, Wand2, Sparkles, User, Camera } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { useProfile, useUploadBodyPhoto } from "@/hooks/useProfile";
import { useWardrobe } from "@/hooks/useWardrobe";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/tryon")({
  head: () => ({
    meta: [
      { title: "Virtual Try-On — Atelier" },
      {
        name: "description",
        content:
          "See how your AI-recommended outfit looks on your body using OOTDiffusion. Upload your photo and let the AI dress you.",
      },
    ],
  }),
  component: TryOnPage,
});

function TryOnPage() {
  const { data: profile } = useProfile();
  const { data: items = [] } = useWardrobe();
  const uploadMutation = useUploadBodyPhoto();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);

  const hasBodyPhoto = Boolean(profile?.body_photo_url);

  // Pick a few wardrobe items for the preview
  const previewItems = items.slice(0, 4);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  }

  function handleGenerate() {
    if (!hasBodyPhoto) return;
    setGenerating(true);
    // Simulate generation (OOTDiffusion via Modal.com — coming soon)
    setTimeout(() => {
      setGenerating(false);
      setGenerated(true);
    }, 3000);
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="flex items-center gap-4">
          <Link
            to="/stylist"
            className="flex items-center gap-2 rounded-full border border-border px-4 py-2 text-xs font-bold uppercase tracking-wider text-muted-foreground transition-colors hover:border-forest hover:text-forest"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Stylist
          </Link>
        </div>
        <div className="mt-6">
          <PageHeader subtitle="OOTDiffusion via Modal.com" title="Virtual Try-On" />
        </div>

        <div className="mt-10 grid gap-8 lg:grid-cols-2">
          {/* ── Left: Body Photo ── */}
          <div>
            <p className="mb-4 text-[0.62rem] font-bold uppercase tracking-[0.28em] text-muted-foreground">
              Your Body Photo
            </p>

            {hasBodyPhoto ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="relative overflow-hidden rounded-[2rem] border border-border shadow-luxe"
              >
                <img
                  src={profile!.body_photo_url!}
                  alt="Your body photo"
                  className="w-full object-cover"
                  style={{ maxHeight: "480px" }}
                />
                <div className="absolute bottom-4 right-4 flex gap-2">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-2 rounded-full bg-ink/80 px-4 py-2 text-xs font-bold uppercase tracking-wider text-beige backdrop-blur-sm transition-colors hover:bg-ink"
                  >
                    <Camera className="h-3.5 w-3.5" /> Change Photo
                  </button>
                </div>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={() => fileInputRef.current?.click()}
                className="flex min-h-[400px] cursor-pointer flex-col items-center justify-center gap-5 rounded-[2rem] border-2 border-dashed border-border transition-all hover:border-forest/50 hover:bg-secondary/20"
              >
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
                  {uploadMutation.isPending ? (
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-forest border-t-transparent" />
                  ) : (
                    <User className="h-7 w-7 text-muted-foreground" />
                  )}
                </div>
                <div className="text-center">
                  <p className="font-semibold text-foreground">
                    {uploadMutation.isPending ? "Uploading…" : "Upload your photo"}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    A clear, full-body photo works best for accurate try-ons
                  </p>
                  <div className="mt-3 flex items-center justify-center gap-2">
                    <Upload className="h-3.5 w-3.5 text-forest" />
                    <span className="text-xs font-bold uppercase tracking-wider text-forest">
                      Click to upload
                    </span>
                  </div>
                </div>
              </motion.div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>

          {/* ── Right: Outfit + Generation ── */}
          <div className="space-y-6">
            <div>
              <p className="mb-4 text-[0.62rem] font-bold uppercase tracking-[0.28em] text-muted-foreground">
                Selected Outfit
              </p>
              <div className="grid grid-cols-2 gap-3">
                {previewItems.length > 0 ? (
                  previewItems.map((item) => (
                    <div
                      key={item.id}
                      className="glass flex flex-col items-center gap-2 rounded-2xl p-4 shadow-soft"
                    >
                      <img
                        src={item.cutout_url}
                        alt={item.name}
                        width={128}
                        height={128}
                        className="h-20 w-20 object-contain drop-shadow"
                      />
                      <div className="text-center">
                        <p className="text-[0.55rem] font-bold uppercase tracking-wider text-muted-foreground">
                          {item.category}
                        </p>
                        <p className="text-xs font-bold">{item.name}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="col-span-2 flex min-h-[200px] items-center justify-center rounded-2xl border border-dashed border-border text-sm text-muted-foreground">
                    No wardrobe items yet.{" "}
                    <Link to="/wardrobe" className="ml-1 text-forest hover:underline">
                      Upload some clothes
                    </Link>
                  </div>
                )}
              </div>
            </div>

            {/* Generate button */}
            <motion.button
              id="generate-tryon-btn"
              onClick={handleGenerate}
              disabled={!hasBodyPhoto || generating || previewItems.length === 0}
              whileHover={hasBodyPhoto && !generating ? { scale: 1.02 } : {}}
              className={cn(
                "flex w-full items-center justify-center gap-3 rounded-full py-5 text-sm font-bold uppercase tracking-[0.2em] shadow-luxe transition-all",
                hasBodyPhoto && !generating
                  ? "bg-ink text-beige hover:bg-ink/90"
                  : "cursor-not-allowed bg-secondary text-muted-foreground",
              )}
            >
              {generating ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-beige border-t-transparent" />
                  Rendering try-on…
                </>
              ) : (
                <>
                  <Wand2 className="h-4 w-4" /> Generate Try-On
                </>
              )}
            </motion.button>

            {!hasBodyPhoto && (
              <p className="text-center text-xs text-muted-foreground">
                Upload your body photo to enable virtual try-on
              </p>
            )}

            {/* OOTDiffusion coming soon state */}
            {generated && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass rounded-[2rem] p-8 text-center shadow-luxe"
              >
                <div className="flex items-center justify-center gap-2 mb-3">
                  <Sparkles className="h-5 w-5 text-forest" />
                  <span className="text-sm font-bold uppercase tracking-wider text-forest">
                    Coming very soon
                  </span>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  OOTDiffusion-powered full-body virtual try-on via{" "}
                  <span className="font-bold text-foreground">Modal.com</span> is in the final
                  integration phase. Your body photo is saved — try-on will render automatically when
                  live.
                </p>
                <div className="mt-5 flex flex-wrap justify-center gap-3 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  <span className="rounded-full border border-border px-3 py-1">OOTDiffusion</span>
                  <span className="rounded-full border border-border px-3 py-1">Modal.com GPU</span>
                  <span className="rounded-full border border-border px-3 py-1">Full-body</span>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
