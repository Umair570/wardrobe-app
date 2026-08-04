import { AnimatePresence, motion } from "motion/react";
import { useRef, useState } from "react";
import { Camera, Trash2, User, X, Upload, Check } from "lucide-react";
import { useProfile, useUploadBodyPhoto, useDeleteBodyPhoto } from "@/hooks/useProfile";
import { cn } from "@/lib/utils";

interface ProfileDrawerProps {
  open: boolean;
  onClose: () => void;
}

export function ProfileDrawer({ open, onClose }: ProfileDrawerProps) {
  const { data: profile } = useProfile();
  const uploadMutation = useUploadBodyPhoto();
  const deleteMutation = useDeleteBodyPhoto();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const displayName = profile?.display_name || profile?.email?.split("@")[0] || "User";
  const initials = displayName.slice(0, 2).toUpperCase();

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      uploadMutation.mutate(file);
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 z-50 bg-ink/50 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Drawer */}
          <motion.aside
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", stiffness: 300, damping: 34 }}
            className="fixed inset-y-0 left-0 z-50 flex w-[320px] flex-col border-r border-border bg-card shadow-luxe"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border px-6 py-5">
              <div>
                <p className="text-[0.6rem] font-bold uppercase tracking-[0.28em] text-muted-foreground">
                  Account
                </p>
                <h2 className="mt-1.5 text-xl uppercase display-xl">Profile</h2>
              </div>
              <button
                onClick={onClose}
                className="rounded-full p-2 text-muted-foreground transition-colors hover:bg-secondary"
                aria-label="Close profile"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-6 py-7 space-y-8">
              {/* Avatar + name */}
              <div className="flex flex-col items-center gap-3 text-center">
                <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-ink text-beige text-xl font-bold uppercase shadow-luxe">
                  {initials}
                  <span className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-forest text-[0.5rem] text-beige">
                    <User className="h-2.5 w-2.5" />
                  </span>
                </div>
                <div>
                  <p className="font-bold text-foreground">{displayName}</p>
                  {profile?.email && (
                    <p className="text-xs text-muted-foreground">{profile.email}</p>
                  )}
                </div>
              </div>

              {/* Body Photo Section */}
              <div>
                <p className="text-[0.62rem] font-bold uppercase tracking-[0.24em] text-muted-foreground mb-3">
                  Body Photo
                </p>
                <p className="text-xs text-muted-foreground mb-4">
                  Upload a full-body photo of yourself so the AI can render virtual try-ons on your body.
                </p>

                {profile?.body_photo_url ? (
                  <div className="space-y-3">
                    <div className="relative overflow-hidden rounded-2xl border border-border">
                      <img
                        src={profile.body_photo_url}
                        alt="Your body photo"
                        className="w-full object-cover max-h-64"
                      />
                      <div className="absolute inset-0 flex items-end justify-end p-3">
                        <span className="flex items-center gap-1 rounded-full bg-forest/90 px-2.5 py-1 text-[0.6rem] font-bold uppercase tracking-widest text-beige">
                          <Check className="h-3 w-3" /> Active
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="flex flex-1 items-center justify-center gap-2 rounded-full border border-border py-2.5 text-xs font-bold uppercase tracking-wider text-foreground transition-colors hover:border-forest hover:text-forest"
                      >
                        <Camera className="h-3.5 w-3.5" /> Replace
                      </button>
                      <button
                        onClick={() => deleteMutation.mutate()}
                        disabled={deleteMutation.isPending}
                        className="flex items-center justify-center gap-2 rounded-full border border-border px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-destructive transition-colors hover:border-destructive"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ) : (
                  <div
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={cn(
                      "flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-10 cursor-pointer transition-all",
                      dragOver
                        ? "border-forest bg-forest/5 scale-[1.02]"
                        : "border-border hover:border-forest/50 hover:bg-secondary/40",
                    )}
                  >
                    {uploadMutation.isPending ? (
                      <div className="h-8 w-8 animate-spin rounded-full border-2 border-forest border-t-transparent" />
                    ) : (
                      <Upload className="h-7 w-7 text-muted-foreground" />
                    )}
                    <div className="text-center">
                      <p className="text-sm font-semibold text-foreground">
                        {uploadMutation.isPending ? "Uploading…" : "Drop photo here"}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        JPEG, PNG or WEBP · max 10 MB
                      </p>
                    </div>
                  </div>
                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handleFileChange}
                />

                {uploadMutation.isError && (
                  <p className="mt-2 text-xs text-destructive">
                    Upload failed. Please try again.
                  </p>
                )}
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
