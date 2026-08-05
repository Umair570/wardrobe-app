import { apiFetch } from "./client";

interface VisualizationItem {
  id: string;
  category?: string;
  image_url?: string;
  cutout_url?: string;
  position?: { x: number; y: number; width: number; height: number };
  z_index?: number;
}

interface VisualizationResponse {
  mode: string;
  items: VisualizationItem[];
  ai_image_url?: string | null;
}

/**
 * Call the visualization endpoint to get a try-on or overlay render.
 */
export async function visualizeOutfit(
  itemIds: string[],
  mode: string = "overlay",
  userBodyPhotoUrl?: string | null,
): Promise<VisualizationResponse> {
  const body: Record<string, unknown> = {
    item_ids: itemIds,
    mode,
  };
  if (userBodyPhotoUrl) {
    body.user_body_photo_url = userBodyPhotoUrl;
  }

  return apiFetch<VisualizationResponse>("/visualization", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
