#!/usr/bin/env python3
"""
Create placeholder logo files for React app
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_logo(size, filename):
    """Create a simple placeholder logo"""
    # Create a new image with a blue background
    img = Image.new('RGB', (size, size), color='#3B82F6')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font_size = size // 4
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Draw text
    text = "PDF2CSV"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Save the image
    img.save(filename)
    print(f"Created {filename} ({size}x{size})")

def main():
    """Create all required logo files"""
    public_dir = "frontend/public"
    
    # Create logos
    create_placeholder_logo(192, f"{public_dir}/logo192.png")
    create_placeholder_logo(512, f"{public_dir}/logo512.png")
    
    print("✅ Placeholder logos created successfully!")

if __name__ == "__main__":
    main()
