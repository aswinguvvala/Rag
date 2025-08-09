#!/usr/bin/env python3
"""
Generate sample placeholder images for testing the background cycling system.
Run this if you want to test the system before downloading real space images.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_image(filename, title, color, size=(1920, 1080)):
    """Create a placeholder image with title and color"""
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default if not available
    try:
        font = ImageFont.truetype("Arial.ttf", 60)
        title_font = ImageFont.truetype("Arial.ttf", 80)
    except:
        font = ImageFont.load_default()
        title_font = font
    
    # Draw title
    text_bbox = draw.textbbox((0, 0), title, font=title_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    draw.text((x, y), title, fill='white', font=title_font)
    draw.text((x, y + 100), f"Placeholder for {filename}", fill='lightgray', font=font)
    
    # Save the image
    output_path = f"static/backgrounds/{filename}"
    img.save(output_path, 'JPEG', quality=85)
    print(f"Created: {output_path}")

def main():
    """Generate all placeholder images"""
    os.makedirs("static/backgrounds", exist_ok=True)
    
    placeholders = [
        ("andromeda_galaxy.jpg", "Andromeda Galaxy", (25, 25, 112)),
        ("eagle_nebula.jpg", "Eagle Nebula", (139, 69, 19)),
        ("whirlpool_galaxy.jpg", "Whirlpool Galaxy", (75, 0, 130)),
        ("horsehead_nebula.jpg", "Horsehead Nebula", (220, 20, 60)),
        ("crab_nebula.jpg", "Crab Nebula", (0, 100, 100)),
        ("earth_from_space.jpg", "Earth from Space", (0, 100, 200)),
        ("jupiter_great_red_spot.jpg", "Jupiter", (200, 100, 50)),
        ("deep_space_field.jpg", "Deep Space", (10, 10, 50))
    ]
    
    for filename, title, color in placeholders:
        create_placeholder_image(filename, title, color)
    
    print("\n✅ All placeholder images created!")
    print("🚀 Run 'streamlit run app.py' to test the cycling background system!")

if __name__ == "__main__":
    main()
