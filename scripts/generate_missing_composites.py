import os
import sys
import json
from PIL import Image, ImageDraw
import shutil
from tqdm import tqdm
import concurrent.futures

# Configuration
TOWN = "ANTRIM"  # Change this to generate for a specific town, or None for all towns
MAX_FILES = None  # Set a limit or None for all files

# Directories
DATA_DIR = "data"
TRUE_POSITIVE_DIR = os.path.join(DATA_DIR, "true_positive_images")
PUBLIC_DIR = "public"
PUBLIC_IMAGES_DIR = os.path.join(PUBLIC_DIR, "images")
PUBLIC_STATIC_DIR = os.path.join(PUBLIC_DIR, "static")

# Get list of towns to process
if TOWN:
    towns = [TOWN]
else:
    towns = [d for d in os.listdir(TRUE_POSITIVE_DIR) if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, d))]

print(f"Processing {len(towns)} towns...")

total_processed = 0
total_created = 0
total_failed = 0
town_stats = {}

# Function to create composite image
def create_side_by_side_image(boxed_path, original_path, output_path):
    try:
        # Open both images
        boxed_img = Image.open(boxed_path)
        original_img = Image.open(original_path)
        
        # Get dimensions
        box_width, box_height = boxed_img.size
        orig_width, orig_height = original_img.size
        
        # Make the original image the same height as the cropped for side-by-side
        new_orig_height = box_height
        new_orig_width = int(orig_width * (new_orig_height / orig_height))
        
        # Resize original image
        resized_orig = original_img.resize((new_orig_width, new_orig_height), Image.LANCZOS)
        
        # Create a new image wide enough for both
        total_width = box_width + new_orig_width + 20  # 20px padding
        composite = Image.new("RGB", (total_width, box_height + 30), (255, 255, 255))
        
        # Paste the boxed image on the left
        composite.paste(boxed_img, (0, 0))
        
        # Paste the original image on the right with some spacing
        composite.paste(resized_orig, (box_width + 20, 0))
        
        # Draw a line to separate the images
        draw = ImageDraw.Draw(composite)
        draw.line([(box_width + 10, 0), (box_width + 10, box_height)], fill=(200, 200, 200), width=1)
        
        # Add labels
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = None
        
        draw.text((10, box_height + 5), "Cropped View", fill=(0, 0, 0), font=font)
        draw.text((box_width + 30, box_height + 5), "Original Context", fill=(0, 0, 0), font=font)
        
        # Save the composite image
        composite.save(output_path, quality=85)
        return True
    except Exception as e:
        print(f"Error creating side-by-side image for {os.path.basename(boxed_path)}: {e}")
        return False

def process_file(town, file_name):
    stats = {"processed": 0, "created": 0, "failed": 0}
    
    # Skip if not a boxed image
    if "_boxed" not in file_name or file_name.startswith("composite_"):
        return stats
    
    # Check if composite already exists
    composite_file_name = f"composite_{file_name}"
    static_town_dir = os.path.join(PUBLIC_STATIC_DIR, town)
    composite_path = os.path.join(static_town_dir, composite_file_name)
    
    if os.path.exists(composite_path):
        return stats
    
    # Create static directory if it doesn't exist
    os.makedirs(static_town_dir, exist_ok=True)
    
    # Source directories
    true_positive_town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
    public_images_town_dir = os.path.join(PUBLIC_IMAGES_DIR, town)
    
    # Search for the boxed file
    source_file = None
    if os.path.exists(os.path.join(true_positive_town_dir, file_name)):
        source_file = os.path.join(true_positive_town_dir, file_name)
    elif os.path.exists(os.path.join(public_images_town_dir, file_name)):
        source_file = os.path.join(public_images_town_dir, file_name)
    
    if not source_file:
        stats["failed"] += 1
        return stats
    
    # Find the original image
    original_file_name = file_name.replace("_boxed", "")
    original_file = None
    if os.path.exists(os.path.join(true_positive_town_dir, original_file_name)):
        original_file = os.path.join(true_positive_town_dir, original_file_name)
    elif os.path.exists(os.path.join(public_images_town_dir, original_file_name)):
        original_file = os.path.join(public_images_town_dir, original_file_name)
    
    if not original_file:
        original_file = source_file  # Fallback to using the boxed image as original
    
    # Create the composite image
    success = create_side_by_side_image(source_file, original_file, composite_path)
    
    # Copy the boxed image to static directory
    static_boxed_path = os.path.join(static_town_dir, file_name)
    if not os.path.exists(static_boxed_path):
        shutil.copy2(source_file, static_boxed_path)
    
    stats["processed"] += 1
    if success:
        stats["created"] += 1
    else:
        stats["failed"] += 1
    
    return stats

# Process each town
for town in towns:
    print(f"\nProcessing town: {town}")
    true_positive_town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
    public_images_town_dir = os.path.join(PUBLIC_IMAGES_DIR, town)
    
    # Get all boxed images
    boxed_files = []
    
    # Look in true_positive_dir
    if os.path.exists(true_positive_town_dir):
        boxed_files.extend([f for f in os.listdir(true_positive_town_dir) 
                          if "_boxed" in f and not f.startswith("composite_") 
                          and os.path.isfile(os.path.join(true_positive_town_dir, f))])
    
    # Look in public_images_dir
    if os.path.exists(public_images_town_dir):
        boxed_files.extend([f for f in os.listdir(public_images_town_dir) 
                          if "_boxed" in f and not f.startswith("composite_") 
                          and os.path.isfile(os.path.join(public_images_town_dir, f))])
    
    # Remove duplicates
    boxed_files = list(set(boxed_files))
    
    # Limit files if specified
    if MAX_FILES:
        boxed_files = boxed_files[:MAX_FILES]
    
    town_stats[town] = {"total": len(boxed_files), "created": 0, "failed": 0}
    print(f"Found {len(boxed_files)} boxed images for {town}")
    
    if not boxed_files:
        continue
    
    # Process files with a progress bar
    with tqdm(total=len(boxed_files), desc=f"Creating composites for {town}") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(process_file, town, file_name): file_name for file_name in boxed_files}
            
            for future in concurrent.futures.as_completed(futures):
                file_name = futures[future]
                try:
                    stats = future.result()
                    total_processed += stats["processed"]
                    total_created += stats["created"]
                    total_failed += stats["failed"]
                    town_stats[town]["created"] += stats["created"]
                    town_stats[town]["failed"] += stats["failed"]
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")
                    total_failed += 1
                    town_stats[town]["failed"] += 1
                
                pbar.update(1)

# Print summary
print("\n===== COMPOSITE IMAGE GENERATION SUMMARY =====")
print(f"Total files processed: {total_processed}")
print(f"Total composite images created: {total_created}")
print(f"Total failures: {total_failed}")
print("\n===== PER-TOWN STATISTICS =====")
for town, stats in town_stats.items():
    success_rate = f"{(stats['created'] / stats['total'] * 100):.1f}%" if stats['total'] > 0 else "N/A"
    print(f"{town}: {stats['created']}/{stats['total']} ({success_rate})")

print("\nDone\!")
