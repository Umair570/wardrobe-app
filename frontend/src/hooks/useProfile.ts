import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchProfile, uploadBodyPhoto, deleteBodyPhoto, type UserProfile } from "@/lib/api";

export function useProfile() {
  return useQuery<UserProfile | null>({
    queryKey: ["profile"],
    queryFn: fetchProfile,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useUploadBodyPhoto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, saveProfile }: { file: File, saveProfile?: boolean }) => uploadBodyPhoto(file, saveProfile),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}

export function useDeleteBodyPhoto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteBodyPhoto,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}
