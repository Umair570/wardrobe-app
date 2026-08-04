import { motion } from "motion/react";
import type { WardrobeItem } from "@/lib/types";

export function ItemCard({
  item,
  index = 0,
  onClick,
}: {
  item: WardrobeItem;
  index?: number;
  onClick?: () => void;
}) {
  return (
    <motion.button
      layout
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.94 }}
      transition={{ duration: 0.45, delay: Math.min(index * 0.05, 0.4) }}
      onClick={onClick}
      className="group glass w-full rounded-3xl p-5 text-left shadow-soft transition-all duration-500 hover:-translate-y-1.5 hover:shadow-luxe"
    >
      <div className="flex h-40 items-center justify-center rounded-2xl bg-secondary/60">
        <img
          src={item.cutout_url}
          alt={item.name}
          width={768}
          height={768}
          loading="lazy"
          className="h-32 w-32 object-contain transition-transform duration-500 group-hover:scale-110"
        />
      </div>
      <p className="mt-4 text-sm font-bold">{item.name}</p>
      <p className="mt-1 text-[0.6rem] font-bold uppercase tracking-[0.2em] text-muted-foreground">
        {item.category} · {item.color}
      </p>
    </motion.button>
  );
}