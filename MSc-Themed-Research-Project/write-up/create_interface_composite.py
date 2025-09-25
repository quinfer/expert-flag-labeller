#!/usr/bin/env python3
"""
Create a composite figure from the expert labeling interface screenshots
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_interface_composite():
    """Create a composite figure showing the complete expert labeling workflow"""
    
    # First, let's check what image files we have available
    print("Looking for interface screenshots...")
    
    # You'll need to save your 4 screenshots with these names:
    screenshot_files = [
        "interface_1_main.png",      # Main interface with dual view
        "interface_2_categories.png", # Category selection 
        "interface_3_detailed.png",   # Detailed classification
        "interface_4_taxonomy.png"    # Full taxonomy
    ]
    
    # Check if files exist
    missing_files = []
    existing_files = []
    
    for filename in screenshot_files:
        if os.path.exists(filename):
            existing_files.append(filename)
            print(f"✓ Found: {filename}")
        else:
            missing_files.append(filename)
            print(f"✗ Missing: {filename}")
    
    if missing_files:
        print(f"\nPlease save your 4 interface screenshots as:")
        for i, filename in enumerate(screenshot_files, 1):
            print(f"{i}. {filename}")
        print("\nThen run this script again.")
        return None
    
    # Load all images
    images = []
    for filename in screenshot_files:
        img = Image.open(filename)
        images.append(img)
        print(f"Loaded: {filename} - Size: {img.size}")
    
    # Calculate dimensions for 2x2 grid
    # We'll resize all images to have similar heights while maintaining aspect ratio
    target_height = 400  # pixels
    
    resized_images = []
    for i, img in enumerate(images):
        # Calculate new width maintaining aspect ratio
        aspect_ratio = img.width / img.height
        new_width = int(target_height * aspect_ratio)
        
        # Resize image
        resized_img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
        resized_images.append(resized_img)
        print(f"Resized image {i+1}: {resized_img.size}")
    
    # Calculate composite dimensions
    # Top row: images 0 and 1
    # Bottom row: images 2 and 3
    top_row_width = resized_images[0].width + resized_images[1].width + 20  # 20px gap
    bottom_row_width = resized_images[2].width + resized_images[3].width + 20
    
    composite_width = max(top_row_width, bottom_row_width) + 40  # 20px margins
    composite_height = (target_height * 2) + 60  # 20px gaps + margins
    
    # Create composite image with white background
    composite = Image.new('RGB', (composite_width, composite_height), 'white')
    
    # Position images in 2x2 grid
    # Top left (a) - Main interface
    x_offset = 20
    y_offset = 20
    composite.paste(resized_images[0], (x_offset, y_offset))
    
    # Top right (b) - Categories
    x_offset = 20 + resized_images[0].width + 20
    composite.paste(resized_images[1], (x_offset, y_offset))
    
    # Bottom left (c) - Detailed classification
    x_offset = 20
    y_offset = 20 + target_height + 20
    composite.paste(resized_images[2], (x_offset, y_offset))
    
    # Bottom right (d) - Full taxonomy
    x_offset = 20 + resized_images[2].width + 20
    composite.paste(resized_images[3], (x_offset, y_offset))
    
    # Add labels (a), (b), (c), (d)
    draw = ImageDraw.Draw(composite)
    
    # Try to use a system font, fallback to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
    
    # Add labels
    labels = ['(a)', '(b)', '(c)', '(d)']
    positions = [
        (25, 25),  # Top left
        (25 + resized_images[0].width + 20, 25),  # Top right
        (25, 25 + target_height + 20),  # Bottom left
        (25 + resized_images[2].width + 20, 25 + target_height + 20)  # Bottom right
    ]
    
    for label, pos in zip(labels, positions):
        # Add white background for label
        bbox = draw.textbbox(pos, label, font=font)
        draw.rectangle([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2], fill='white', outline='black')
        draw.text(pos, label, fill='black', font=font)
    
    # Save composite
    output_path = "plots/expert_labeling_interface_composite.png"
    composite.save(output_path, 'PNG', dpi=(300, 300))
    
    print(f"\n✓ Composite figure created: {output_path}")
    print(f"Dimensions: {composite.size}")
    print(f"This figure shows the complete expert labeling workflow across 4 interface views.")
    
    return output_path

if __name__ == "__main__":
    result = create_interface_composite()
    if result:
        print(f"\nSuccess! The composite figure is ready for your paper.")
    else:
        print(f"\nPlease save your screenshots and run again.")
