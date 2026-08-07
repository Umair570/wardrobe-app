"use client";

import * as React from "react";
import type { ClothingItem } from "@/types";
import { getClothingItems, deleteItem } from "@/lib/api/wardrobe";

interface WardrobeContextValue {
  items: ClothingItem[];
  loading: boolean;
  error: string | null;
  favorites: Record<string, boolean>;
  toggleFavorite: (id: string) => void;
  removeItem: (id: string) => Promise<void>;
  refresh: () => Promise<void>;
}

const WardrobeContext = React.createContext<WardrobeContextValue | undefined>(undefined);

export function WardrobeProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<ClothingItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [favorites, setFavorites] = React.useState<Record<string, boolean>>({});

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getClothingItems();
      setItems(data);
    } catch (err: unknown) {
      // Gracefully handle when user is not authenticated or backend is down
      const message = err instanceof Error ? err.message : "Failed to load wardrobe";
      console.warn("[WardrobeProvider] Could not load items:", message);
      setError(message);
      setItems([]);
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

  const removeItem = React.useCallback(async (id: string) => {
    try {
      await deleteItem(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      console.error("[WardrobeProvider] Failed to delete item", err);
      throw err;
    }
  }, []);

  return (
    <WardrobeContext.Provider value={{ items, loading, error, favorites, toggleFavorite, removeItem, refresh }}>
      {children}
    </WardrobeContext.Provider>
  );
}

export function useWardrobeContext() {
  const ctx = React.useContext(WardrobeContext);
  if (!ctx) throw new Error("useWardrobeContext must be used within WardrobeProvider");
  return ctx;
}
