import sys
import os
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from ml.segmentation.inference import process_image

img_path = "upload images/image 4.jpg"

try:
    seg_result = process_image(img_path, output_directory="ml/.outputs")
    for item in seg_result.get("items", []):
        mask_path = item["path"]
        
        img = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
        pixels = bgr[alpha > 0]
        
        Z = np.float32(pixels)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = 3
        _, label, centers = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        centers_uint8 = np.uint8(centers)
        centers_uint8_3d = centers_uint8.reshape(K, 1, 3)
        centers_hsv = cv2.cvtColor(centers_uint8_3d, cv2.COLOR_BGR2HSV).reshape(K, 3)
        saturations = centers_hsv[:, 1].astype(np.float32)
        
        import collections
        counts = np.bincount(label.flatten(), minlength=K)
        
        print("---- IMAGE 4 GREEN TEE RESULTS ----")
        for i in range(K):
            vol = (counts[i] / np.sum(counts)) * 100
            sat = saturations[i]
            rgb = centers_uint8[i][::-1] 
            print(f"Cluster {i}: Vol {vol:.1f}% | Sat {sat:.1f} | RGB {rgb}")
except Exception as e:
    print("Error:", e)
