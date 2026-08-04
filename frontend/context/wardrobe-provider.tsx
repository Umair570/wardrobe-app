"use client";

import * as React from "react";
import type { ClothingItem } from "@/types";
import { getClothingItems } from "@/lib/api/wardrobe";

interface WardrobeContextValue {
  items: ClothingItem[];
  loading: boolean;
  favorites: Record<string, boolean>;
  toggleFavorite: (id: string) => void;
  refresh: () => Promise<void>;
}

const WardrobeContext = React.createContext<WardrobeContextValue | undefined>(undefined);

export function WardrobeProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<ClothingItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [favorites, setFavorites] = React.useState<Record<string, boolean>>({});

  const refresh = React.useCallback(async () => {
    setLoading(true);
    try {
      setItems(await getClothingItems());
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    refresh();
  }, [refresh]);

  const toggleFavorite = React.useCallback((id: string) => {
    setFavorites((f) => ({ ...f, [id]: !f[id] }));
  }, []);

  return (
    <WardrobeContext.Provider value={{ items, loading, favorites, toggleFavorite, refresh }}>
      {children}
    </WardrobeContext.Provider>
  );
}

export function useWardrobeContext() {
  const ctx = React.useContext(WardrobeContext);
  if (!ctx) throw new Error("useWardrobeContext must be used within WardrobeProvider");
  return ctx;
}
