from pathlib import Path
from PIL import Image

def create_output_directory(output_directory: str):
    Path(output_directory).mkdir(parents=True, exist_ok=True)

def load_image(image_path: str):
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    return Image.open(image_path).convert("RGB")