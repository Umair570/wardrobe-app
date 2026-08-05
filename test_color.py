import sys
import os
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from ml.classification.inference import _nearest_color_name

print("=== COLOR REVERSAL TEST ===")
color_name = _nearest_color_name(np.array([35, 16, 15]))
print(f"BGR Flip [35, 16, 15] -> {color_name}")
