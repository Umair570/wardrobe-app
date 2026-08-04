import { useState } from "react";
import { UploadCloud, CheckCircle2 } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/LuxButton";
import { ingestGarment } from "@/lib/api";

export function UploadModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState<"idle" | "uploading" | "done">("idle");
  const [fileName, setFileName] = useState<string | null>(null);

  async function handleFile(file: File) {
    setFileName(file.name);
    setStatus("uploading");
    await ingestGarment(file);
    setStatus("done");
  }

  return (
    <Modal open={open} onClose={onClose} title="Add items">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) void handleFile(file);
        }}
        className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 text-center transition-colors duration-300 ${
          dragging ? "border-forest bg-secondary" : "border-border"
        }`}
      >
        {status === "done" ? (
          <>
            <CheckCircle2 className="h-8 w-8 text-forest" />
            <p className="mt-4 text-sm font-bold">Background stripped & embedded</p>
            <p className="mt-1 text-xs text-muted-foreground">{fileName}</p>
          </>
        ) : status === "uploading" ? (
          <>
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-forest" />
            <p className="mt-4 text-sm font-bold">Running the cutout pipeline…</p>
            <p className="mt-1 text-xs text-muted-foreground">Segmenting, then embedding</p>
          </>
        ) : (
          <>
            <UploadCloud className="h-8 w-8 text-forest" />
            <p className="mt-4 text-sm font-bold">Drop a garment photo</p>
            <p className="mt-1 text-xs text-muted-foreground">PNG or JPG, one piece per shot</p>
            <label className="mt-6">
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void handleFile(file);
                }}
              />
              <span className="inline-flex h-11 cursor-pointer items-center rounded-full bg-ink px-6 text-xs font-semibold uppercase tracking-[0.14em] text-beige">
                Browse files
              </span>
            </label>
          </>
        )}
      </div>

      {status === "done" && (
        <Button
          className="mt-5 w-full"
          onClick={() => {
            setStatus("idle");
            onClose();
          }}
        >
          Done
        </Button>
      )}
    </Modal>
  );
}