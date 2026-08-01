# AI Wardrobe Assistant — ML Pipeline (MVP)

This repository contains the Machine Learning (CV/NLP) engine for the AI Wardrobe App MVP. The pipeline is responsible for taking raw photos of clothing (such as flatlays, bed-lays, or selfies), perfectly extracting each garment from the background, and dynamically analyzing it to produce rich fashion metadata (category, style, color, pattern, etc.).

---

## 🧠 Pipeline Architecture

The Machine Learning engine is broken into two sequential modules orchestrated by `ml/pipeline.py`.

### 1. Segmentation (`ml/segmentation`)
Converts noisy, poorly-lit images into isolated, transparent PNG items.
* **CLIPSeg**: Runs first to generate a coarse semantic heatmap of clothing items (e.g., locating the "pants" vs the "shirt"). It maps out bounding boxes for these regions.
* **SAM2 (Segment Anything Model 2 - Tiny)**: An extremely powerful zero-shot segmentation model by Ultralytics. SAM2 receives the bounding boxes from CLIPSeg and traces completely pixel-perfect contours around the clothing. 
  * *Why SAM2 over U2Net/RemBG?* SAM2 flawlessly understands overlapping garments, shadows, and low-contrast flatlays (e.g., black jeans on a dark grey bed), which traditionally break standard background removers.

### 2. Classification (`ml/classification`)
Takes the segmented transparent PNGs and performs zero-shot feature extraction.
* **FashionCLIP**: A HuggingFace vision-language model trained exclusively on fashion catalogs. It analyzes the garment to extract zero-shot features across multiple categories (e.g., `Category: Sweater`, `Type: Hoodie`, `Style: Streetwear`, `Season: Spring/Fall`, `Pattern: Plaid/Solid/Graphic`).
* **KMeans HSV Color Extraction**: A custom algorithm running in the HSV color space. It isolates only the foreground pixels of the clothing and strongly weights "saturation" and "cluster volume." This prevents the algorithm from accidentally tagging the inside of a white collar or a grey washing tag as the dominant color of a blue jacket. The extracted color is mathematically mapped to a strict bank of **71 standard fashion colors**.

---

## 📁 Directory Structure

```text
wardrobe-app/
│
├── requirements.txt                   # Strict ML dependencies (torch, ultralytics, etc.)
│
└── ml/
    ├── pipeline.py                    # THE MAIN ENTRYPOINT (Use this)
    │
    ├── segmentation/
    │   ├── model.py                   # Loads SAM2 and CLIPSeg into memory
    │   ├── inference.py               # Houses process_image() logic
    │   └── utils.py                   # Image loading & folder creation
    │
    ├── classification/
    │   ├── model.py                   # Loads FashionCLIP and the 71-Color Dictionary
    │   └── inference.py               # Houses classify_item() logic
    │
    ├── test_images/                   # Upload raw testing jpegs here
    └── outputs/                       # Segmented PNGs are dumped here
```

---

## 🚀 Setup & Installation

The ML pipeline requires Python 3.10+ and uses PyTorch.

1. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate      # On Windows
   # source venv/bin/activate        # On Mac/Linux
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

*(Note: When you run the pipeline for the very first time, HuggingFace and Ultralytics will automatically download their model weights (`sam2_t.pt` and `fashion-clip`) directly to your system cache. You need an active internet connection on the first run).*

---

## 💻 How to Run (For Backend Integrators)

Backend developers (e.g., FastAPI) **should not** call the segmentation or classification scripts manually. You should only interact with the unified orchestrator: `process_wardrobe_upload`.

### Example Integration

```python
from ml.pipeline import process_wardrobe_upload

# Call the pipeline synchronously. 
# WARNING: If using FastAPI, use run_in_threadpool to prevent event loop blocking.
result = process_wardrobe_upload("ml/test_images/image 2.jpg")

print(result)
```

### Expected Output Payload (The JSON Schema)
The unified function returns a strict payload ready to be parsed into NoSQL documents:

```json
{
  "success": true,
  "image_source": "image 2.jpg",
  "total_items": 1,
  "processing_time_sec": 3.42,
  "items": [
    {
      "segmentation_file": "image 2_item_0.png",
      "segmentation_path": "ml/outputs/image 2_item_0.png",
      "area_ratio": 0.24,
      "category": "sweater",
      "type": "hoodie",
      "style": "streetwear",
      "season": "spring/fall",
      "pattern": "solid",
      "color": "beige",
      "tags": ["beige", "hoodie", "solid", "spring/fall", "streetwear", "sweater"],
      "confidence_scores": {
        "category": 0.98,
        "type": 0.95,
        "style": 0.65,
        "season": 0.81,
        "pattern": 0.99
      }
    }
  ]
}
```

### Failure Output Payload
If the user uploads a blurry photo or an image with no detectable clothing, the pipeline safely returns an error schema:

```json
{
  "success": false,
  "error": "The image is too blurry. Please upload a clear photo of the clothing.",
  "code": "BLURRY_IMAGE"  // Example codes: BLURRY_IMAGE, NO_CLOTHING, SEG_ERROR
}
```

---

## 🛡️ Edge Cases Handled

The `ml/pipeline.py` is fortified to prevent API crashes:
1. **Blur Rejection:** Runs an OpenCV Laplacian Variance check. If the user uploads a highly out-of-focus image, it instantly rejects it with `code: BLURRY_IMAGE`.
2. **Missing Clothing:** If CLIPSeg fails to identify any clothing in the photo (e.g., the user uploaded a picture of a car), the pipeline safely returns `success: False` with `code: NO_CLOTHING`.
3. **RAM Threshold:** Designed to operate on CPU instances, though it requires at least **2GB to 4GB of Server RAM** to hold both FashionCLIP and SAM2 in memory concurrently.