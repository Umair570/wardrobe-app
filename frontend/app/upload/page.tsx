"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, Check, Loader2 } from "lucide-react";
import { AppNav } from "@/components/layout/app-nav";
import { Button } from "@/components/ui/button";
import { ImagePlaceholder } from "@/components/ui/image-placeholder";
import { cn } from "@/lib/utils";
import { uploadGarment } from "@/lib/api/wardrobe";

type Mode = "single" | "multi" | "outfit";
type DropState = "idle" | "drag-active" | "uploading" | "processing" | "success" | "error";

const TIPS = [
  "Lay flat on plain fabric",
  "Daylight, no direct flash",
  "One garment per frame in single mode",
  "Keep hangers out of shot",
  "Shoot straight on, not angled",
];

export default function UploadPage() {
  const [mode, setMode] = React.useState<Mode>("single");
  const [dropState, setDropState] = React.useState<DropState>("idle");
  const [progress, setProgress] = React.useState(0);
  const [resultText, setResultText] = React.useState("");
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  async function handleChoosePhoto() {
    setDropState("uploading");
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((p) => Math.min(p + 12, 90));
    }, 120);

    await new Promise((r) => setTimeout(r, 800));
    clearInterval(interval);
    setProgress(100);
    setDropState("processing");

    const res = await uploadGarment(new File([], "mock.jpg"));
    await new Promise((r) => setTimeout(r, 600));

    if (res.ok) {
      setResultText(`Garment tagged: ${res.taggedName}.`);
      setDropState("success");
    } else {
      setResultText("Scan failed — try better lighting.");
      setDropState("error");
    }
  }

  function handleSimulateFail() {
    setDropState("error");
    setResultText("Scan failed — try better lighting.");
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    if (dropState === "idle") setDropState("drag-active");
  }

  function handleDragLeave() {
    if (dropState === "drag-active") setDropState("idle");
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    handleChoosePhoto();
  }

  const isBusy = dropState === "uploading" || dropState === "processing";

  return (
    <div className="min-h-screen bg-cream dark:bg-[#161611]">
      <AppNav />
      <div className="mx-auto max-w-4xl px-6 pb-24 pt-11 md:px-12">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <span className="font-mono text-[11.5px] font-semibold tracking-wide text-gold">ADD TO THE RAIL</span>
          <h1 className="mt-2 font-heading text-[clamp(30px,3.6vw,44px)] font-semibold text-ink dark:text-cream">
            Upload Clothes
          </h1>
          <p className="mt-2 font-sans text-[15px] text-ink/60 dark:text-cream/60">
            Lay the garment flat on a plain surface — the tagger reads colour, fabric and cut.
          </p>
        </motion.div>

        <div className="mt-6 flex flex-wrap gap-2.5">
          {(["single", "multi", "outfit"] as Mode[]).map((m) => (
            <motion.button
              key={m}
              whileTap={{ scale: 0.97 }}
              onClick={() => setMode(m)}
              className={cn(
                "rounded-full px-[18px] py-2.5 font-mono text-[11.5px] tracking-wide transition-colors",
                mode === m
                  ? "bg-ink text-cream dark:bg-cream dark:text-ink"
                  : "border border-ink/15 bg-card text-ink hover:border-forest/30 dark:border-cream/20 dark:text-cream"
              )}
            >
              {m === "single" ? "SINGLE ITEM" : m === "multi" ? "MULTIPLE ITEMS" : "OUTFIT PHOTO"}
            </motion.button>
          ))}
        </div>

        <div className="mt-6 grid gap-6 md:grid-cols-[1.6fr_1fr]">
          <motion.div
            animate={{
              scale: dropState === "drag-active" ? 1.02 : 1,
              borderColor: dropState === "drag-active" ? "rgba(47,79,63,0.6)" : undefined,
            }}
            transition={{ type: "spring", stiffness: 300, damping: 22 }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
              "relative rounded-lg border-2 border-dashed bg-card p-16 text-center transition-colors",
              dropState === "drag-active"
                ? "border-forest dark:border-[#8fbfa4]"
                : "border-ink/18 dark:border-cream/20",
              dropState === "success" && "border-forest/50",
              dropState === "error" && "border-[#B5502F]/50"
            )}
          >
            <AnimatePresence mode="wait">
              {dropState === "success" ? (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex flex-col items-center"
                >
                  <motion.div
                    initial={{ pathLength: 0 }}
                    animate={{ scale: [0.8, 1.1, 1] }}
                    className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-forest/10 dark:bg-[#8fbfa4]/15"
                  >
                    <Check className="h-8 w-8 text-forest dark:text-[#8fbfa4]" strokeWidth={2} />
                  </motion.div>
                  <p className="mb-4 font-sans text-sm font-semibold text-forest dark:text-[#8fbfa4]">{resultText}</p>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="h-32 w-24 overflow-hidden rounded-lg shadow-lg"
                  >
                    <ImagePlaceholder label="Added" />
                  </motion.div>
                  <Button className="mt-6" variant="secondary" size="sm" onClick={() => setDropState("idle")}>
                    Upload another
                  </Button>
                </motion.div>
              ) : isBusy ? (
                <motion.div key="busy" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center">
                  <Loader2 className="mb-4 h-10 w-10 animate-spin text-forest dark:text-[#8fbfa4]" />
                  <p className="mb-4 font-sans text-sm text-ink/60 dark:text-cream/60">
                    {dropState === "uploading" ? "Uploading…" : "Analyzing garment…"}
                  </p>
                  <div className="h-1.5 w-48 overflow-hidden rounded-full bg-cream-muted dark:bg-white/10">
                    <motion.div
                      className="h-full rounded-full bg-forest dark:bg-[#8fbfa4]"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ ease: "easeOut" }}
                    />
                  </div>
                </motion.div>
              ) : (
                <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <motion.div
                    animate={dropState === "drag-active" ? { scale: 1.1 } : { y: [0, -6, 0] }}
                    transition={
                      dropState === "drag-active"
                        ? { type: "spring", stiffness: 400 }
                        : { duration: 3, repeat: Infinity, ease: "easeInOut" }
                    }
                    className="mx-auto mb-[18px] flex w-fit items-center justify-center"
                  >
                    <UploadCloud className="h-8 w-8 text-ink dark:text-cream" strokeWidth={1.6} />
                  </motion.div>
                  <h3 className="mb-2 font-heading text-2xl font-semibold text-ink dark:text-cream">
                    {dropState === "drag-active" ? "Release to upload" : "Drop the garment here"}
                  </h3>
                  <p className="mb-6 font-sans text-sm text-ink/55 dark:text-cream/55">
                    Drag a photo in, or tap to open your camera.
                  </p>
                  <div className="flex flex-wrap justify-center gap-3">
                    <Button onClick={handleChoosePhoto} disabled={isBusy}>
                      Choose photo
                    </Button>
                    <Button variant="outline" onClick={handleSimulateFail}>
                      Simulate failed scan
                    </Button>
                  </div>
                  {dropState === "error" && (
                    <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-5 font-sans text-[13.5px] font-semibold text-[#B5502F]">
                      {resultText}
                    </motion.p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
            <input ref={fileInputRef} type="file" accept="image/*" className="hidden" />
          </motion.div>

          <div className="rounded-lg bg-card p-6 shadow-[0_4px_16px_rgba(30,30,30,0.06)]">
            <p className="mb-2.5 font-mono text-[10.5px] tracking-wide text-ink/50 dark:text-cream/50">CARE LABEL · TIPS</p>
            <hr className="my-3.5 border-ink/8 dark:border-cream/10" />
            <div className="flex flex-col gap-3">
              {TIPS.map((tip) => (
                <p key={tip} className="font-sans text-[13.5px] text-ink dark:text-cream">
                  ✓ {tip}
                </p>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
