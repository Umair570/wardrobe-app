import { useQuery } from "@tanstack/react-query";
import { fetchWardrobe } from "@/lib/api";

export function useWardrobe() {
  return useQuery({ queryKey: ["wardrobe"], queryFn: fetchWardrobe });
}