from rembg import remove, new_session
from PIL import Image
import time
import cv2
import numpy as np

for model_name in ["u2net", "isnet-general-use"]:
    print(f"\nEvaluating {model_name}...")
    session = new_session(model_name)
    
    img = Image.open("ml/test_images/image 1.jpg").convert("RGB")
    
    start = time.time()
    out = remove(img, session=session)
    elapsed = time.time() - start
    
    print(f"{model_name} took {elapsed:.2f}s")
    out.save(f"ml/outputs/test_{model_name}.png")
