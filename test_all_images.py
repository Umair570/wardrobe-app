import sys
import os
import glob
import json

# Suppress Torch/HF logs
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from ml.pipeline import process_wardrobe_upload

test_images_dir = "upload images"
images = glob.glob(f"{test_images_dir}/*.*")

with open("ml_test_results.log", "w") as f:
    for img in images:
        if "gitkeep" in img: continue
        f.write(f"\n--- Testing: {img} ---\n")
        try:
            result = process_wardrobe_upload(img)
            f.write(json.dumps(result, indent=2) + "\n")
        except Exception as e:
            f.write(f"ERROR: {str(e)}\n")
