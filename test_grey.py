import sys
import os
import cv2
import numpy as np
from sklearn.cluster import KMeans

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from ml.classification.inference import _nearest_color_name

img_path = 'upload images/image 4.jpg'
image_bgr = cv2.imread(img_path)
image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

h, w, c = image_rgb.shape
alpha = np.ones((h, w), dtype=np.uint8) * 255
white_mask = (image_rgb[:,:,0] > 240) & (image_rgb[:,:,1] > 240) & (image_rgb[:,:,2] > 240)
alpha[white_mask] = 0

fg_mask = alpha > 128
fg_pixels = image_rgb[fg_mask]
indices = np.random.choice(len(fg_pixels), min(len(fg_pixels), 8000), replace=False)
fg_pixels = fg_pixels[indices]

kmeans = KMeans(n_clusters=3, n_init=5, random_state=42)
kmeans.fit(fg_pixels.astype(np.float32))

centers = kmeans.cluster_centers_
counts = np.bincount(kmeans.labels_)

centers_uint8 = np.clip(centers, 0, 255).astype(np.uint8).reshape(1, -1, 3)
centers_hsv = cv2.cvtColor(centers_uint8, cv2.COLOR_RGB2HSV).reshape(-1, 3)
saturations = centers_hsv[:, 1].astype(np.float32)

import json

out_data = {
    "clusters": []
}

for i in range(len(centers)):
    vol = (counts[i] / np.sum(counts)) * 100
    rgb = centers[i].astype(int).tolist()
    out_data["clusters"].append({"vol": vol, "sat": float(saturations[i]), "rgb": rgb})

max_idx = int(np.argmax(saturations))
largest_idx = int(np.argmax(counts))

if np.max(saturations) > 12:
    best_idx = max_idx
else:
    best_idx = largest_idx

out_data["chosen_idx"] = best_idx
out_data["chosen_rgb"] = centers[best_idx].astype(int).tolist()
out_data["classified"] = _nearest_color_name(centers[best_idx])

with open("test_grey_data.json", "w") as f:
    json.dump(out_data, f, indent=2)

