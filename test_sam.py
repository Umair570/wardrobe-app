from ultralytics import SAM, FastSAM
import time
from pathlib import Path

img_path = "ml/test_images/image 1.jpg"

print("Benchmarking SAM models on CPU...")

for model_name in ["sam2_t.pt", "FastSAM-s.pt"]:
    print(f"\nLoading {model_name}...")
    if "Fast" in model_name:
        model = FastSAM(model_name)
    else:
        model = SAM(model_name)
    
    # Warmup
    _ = model(img_path, bboxes=[100, 100, 300, 300], verbose=False)
    
    start = time.time()
    _ = model(img_path, bboxes=[100, 100, 300, 300], verbose=False)
    elapsed = time.time() - start
    
    print(f"{model_name} took {elapsed:.3f}s per image inference (after warmup)")
