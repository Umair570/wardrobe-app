import os
import glob
from PIL import Image

output_files = glob.glob('ml/outputs/*.png')
if not output_files:
    print("No output files found!")
    exit()

def print_ascii_art(img_path):
    print(f"\n--- {os.path.basename(img_path)} ---")
    try:
        img = Image.open(img_path)
        if img.mode != 'RGBA':
            print("Image is not RGBA!")
            return
            
        # Resize aggressively to fit in standard terminal width (120 cols) 
        # Consoles have 2:1 character aspect ratio height:width, so we scale height by half
        img = img.resize((50, 25))
        pixels = img.load()
        
        for y in range(img.height):
            line = ""
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                # High opacity
                if a > 200:
                    line += "██"
                # Partial opacity (glitchy edges)
                elif a > 50:
                    line += "░░"
                # Transparent
                else:
                    line += "  "
            print(line)
            
    except Exception as e:
        print(f"Error: {e}")

# Just print the first 4 output files to see what they look like
for f in sorted(output_files)[:4]:
    print_ascii_art(f)
