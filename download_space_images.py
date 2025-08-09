#!/usr/bin/env python3
"""
Space Images Download Helper
============================

This script provides direct URLs to high-quality space images from NASA, ESA/Hubble, 
and other free sources that can be manually downloaded for the IntelliSearch background cycling system.

Run this script to get download instructions and URLs.
"""

import json
import os

def print_download_instructions():
    """Print instructions for downloading space background images"""
    
    print("🌌 IntelliSearch Background Images Download Guide")
    print("=" * 55)
    print()
    print("Please manually download the following high-quality space images:")
    print("All images are from NASA/ESA (public domain) or free stock sources.")
    print()
    
    # High-quality space images with direct URLs
    images = [
        {
            "filename": "andromeda_galaxy.jpg",
            "title": "Andromeda Galaxy",
            "description": "The nearest major galaxy to the Milky Way",
            "source": "NASA/ESA Hubble",
            "url": "https://science.nasa.gov/wp-content/uploads/2023/05/potw1726a.jpg",
            "alternative_search": "NASA Hubble Andromeda Galaxy M31",
            "size_guide": "1920x1080 or higher"
        },
        {
            "filename": "eagle_nebula.jpg", 
            "title": "Eagle Nebula - Pillars of Creation",
            "description": "Famous star-forming region in Serpens constellation",
            "source": "NASA/ESA Hubble",
            "url": "https://science.nasa.gov/wp-content/uploads/2023/05/heic1501a.jpg",
            "alternative_search": "NASA Hubble Pillars of Creation Eagle Nebula",
            "size_guide": "1920x1080 or higher"
        },
        {
            "filename": "whirlpool_galaxy.jpg",
            "title": "Whirlpool Galaxy",
            "description": "Classic spiral galaxy M51",
            "source": "NASA/ESA Hubble",
            "url": "https://science.nasa.gov/wp-content/uploads/2023/05/potw1019a.jpg",
            "alternative_search": "NASA Hubble Whirlpool Galaxy M51",
            "size_guide": "1920x1080 or higher"
        },
        {
            "filename": "horsehead_nebula.jpg",
            "title": "Horsehead Nebula",
            "description": "Dark nebula in Orion constellation",
            "source": "NASA/ESA Hubble",
            "url": "https://science.nasa.gov/wp-content/uploads/2023/05/heic1307a.jpg",
            "alternative_search": "NASA Hubble Horsehead Nebula Orion",
            "size_guide": "1920x1080 or higher"
        },
        {
            "filename": "crab_nebula.jpg",
            "title": "Crab Nebula",
            "description": "Supernova remnant in Taurus",
            "source": "NASA/ESA Hubble",
            "url": "https://science.nasa.gov/wp-content/uploads/2023/05/heic0515a.jpg",
            "alternative_search": "NASA Hubble Crab Nebula M1",
            "size_guide": "1920x1080 or higher"
        },
        {
            "filename": "earth_from_space.jpg",
            "title": "Earth from Space",
            "description": "Our home planet from the International Space Station",
            "source": "NASA",
            "url": "https://www.nasa.gov/wp-content/uploads/2015/01/as11-44-6551orig.jpg",
            "alternative_search": "NASA Earth from space ISS blue marble",
            "size_guide": "1920x1080 or higher"
        },
        {
            "filename": "jupiter_great_red_spot.jpg",
            "title": "Jupiter's Great Red Spot",
            "description": "The giant storm on Jupiter",
            "source": "NASA/Juno",
            "url": "https://www.nasa.gov/wp-content/uploads/2017/07/pia21775.jpg",
            "alternative_search": "NASA Juno Jupiter Great Red Spot",
            "size_guide": "1920x1080 or higher"
        },
        {
            "filename": "deep_space_field.jpg",
            "title": "Hubble Deep Field",
            "description": "Thousands of distant galaxies",
            "source": "NASA/ESA Hubble",
            "url": "https://science.nasa.gov/wp-content/uploads/2023/05/hst_udf_wfc3ir.jpg",
            "alternative_search": "NASA Hubble Ultra Deep Field galaxies",
            "size_guide": "1920x1080 or higher"
        }
    ]
    
    for i, img in enumerate(images, 1):
        print(f"{i}. {img['title']}")
        print(f"   📁 Save as: static/backgrounds/{img['filename']}")
        print(f"   🔗 URL: {img['url']}")
        print(f"   📏 Size: {img['size_guide']}")
        print(f"   🔍 Alternative: Search '{img['alternative_search']}' on NASA's website")
        print()
    
    print("📋 DOWNLOAD INSTRUCTIONS:")
    print("1. Right-click each URL above and 'Save Link As...'")
    print("2. Save to the 'static/backgrounds/' directory")
    print("3. Use the exact filename shown (important for the cycling system)")
    print("4. Ensure images are in JPG format and at least 1920x1080 resolution")
    print("5. If a URL doesn't work, use the alternative search terms on:")
    print("   - https://science.nasa.gov/mission/hubble/multimedia/hubble-images/")
    print("   - https://esahubble.org/images/archive/wallpapers/")
    print("   - https://www.nasa.gov/gallery/")
    print()
    print("⚡ QUICK START:")
    print("You can also use any high-quality space images you find elsewhere.")
    print("Just rename them to match the filenames above and place them in static/backgrounds/")
    print()
    
    # Alternative free sources
    print("🆓 ALTERNATIVE FREE SOURCES:")
    print("- Pexels.com (search: 'space', 'galaxy', 'nebula')")
    print("- Unsplash.com (search: 'astronomy', 'space', 'cosmos')")
    print("- Pixabay.com (search: 'space', 'universe', 'astronomy')")
    print("- NASA Image Gallery: https://images.nasa.gov/")
    print()
    
    print("🎯 After downloading, run 'streamlit run app.py' to see the cycling backgrounds!")

def create_sample_images_script():
    """Create a script to generate placeholder images for testing"""
    script_content = '''#!/usr/bin/env python3
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
    
    print("\\n✅ All placeholder images created!")
    print("🚀 Run 'streamlit run app.py' to test the cycling background system!")

if __name__ == "__main__":
    main()
'''
    
    with open("create_placeholder_images.py", "w") as f:
        f.write(script_content)
    
    print("📝 Created 'create_placeholder_images.py' script for testing.")
    print("   Run: python create_placeholder_images.py")
    print("   This will create placeholder images to test the cycling system.")

if __name__ == "__main__":
    print_download_instructions()
    print("\n" + "=" * 55)
    create_sample_images_script()