import { AnimatePresence, motion } from "motion/react";
import { X } from "lucide-react";
import type { WardrobeItem } from "@/lib/types";

export function ItemDetailPanel({
  item,
  onClose,
  onDelete,
}: {
  item: WardrobeItem | null;
  onClose: () => void;
  onDelete?: (id: string) => void;
}) {
  return (
    <AnimatePresence>
      {item && (
        <>
          <motion.div
            className="fixed inset-0 z-40 bg-ink/40 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 280, damping: 32 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-md overflow-y-auto border-l border-border bg-card p-8"
          >
            <div className="flex justify-end">
              <button
                onClick={onClose}
                aria-label="Close details"
                className="rounded-full p-2 text-muted-foreground transition-colors hover:bg-secondary"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="flex h-64 items-center justify-center rounded-3xl bg-secondary/70">
              <img
                src={item.cutout_url}
                alt={item.name}
                width={768}
                height={768}
                className="h-52 w-52 object-contain animate-float-slow"
              />
            </div>
            <h2 className="mt-8 text-3xl uppercase display-xl">{item.name}</h2>
            <dl className="mt-8 space-y-4">
              {[
                ["Category", item.category],
                ["Colour", item.color],
                ["Season", item.season],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-border pb-3">
                  <dt className="text-[0.6rem] font-bold uppercase tracking-[0.22em] text-muted-foreground">
                    {k}
                  </dt>
                  <dd className="text-sm font-semibold capitalize">{v}</dd>
                </div>
              ))}
            </dl>
            <div className="mt-6 flex flex-wrap gap-2">
              {item.tags.map((t) => (
                <span
                  key={t}
                  className="rounded-full bg-forest/10 px-3 py-1.5 text-[0.6rem] font-bold uppercase tracking-[0.18em] text-forest"
                >
                  {t}
                </span>
              ))}
            </div>

            <div className="mt-12">
              <button
                onClick={() => {
                  if (window.confirm("Are you sure you want to permanently delete this item?")) {
                    onDelete?.(item.id);
                  }
                }}
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-red-500/10 py-4 text-xs font-bold uppercase tracking-widest text-red-600 transition-colors hover:bg-red-500/20"
              >
                Delete Garment
              </button>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}