import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWardrobe, deleteWardrobeItem } from "@/lib/api";

export function useWardrobe() {
  return useQuery({ queryKey: ["wardrobe"], queryFn: fetchWardrobe });
}

export function useDeleteWardrobeItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteWardrobeItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wardrobe"] });
    },
  });
}