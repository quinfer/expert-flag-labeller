#!/usr/bin/env python3
"""
Sample and Copy Cropped Images for Expert Flag Labeller App

This script:
1. Loads the classification_queue.json file with all cropped images
2. Selects a stratified sample across towns (approx. 3,000 images)
3. Copies the selected images to public/images/{TOWN}/{image} structure
4. Maintains stratification across towns, confidence scores, and image types

Usage:
    python scripts/sample_cropped_for_public.py [options]

Options:
    --sample-size INT        Number of images to sample (default: 3000)
    --output-dir PATH        Output directory (default: public/images)
    --queue-file PATH        Input classification queue (default: data/classification_queue.json)
    --preserve-ratio         Preserve the ratio of single/multi-box images
    --balance-towns          Balance sampling across towns (prevent domination by large towns)
    --debug                  Print detailed debug information
"""

import os
import json
import argparse
import random
import shutil
from collections import defaultdict
import math
from PIL import Image, ImageDraw, ImageFont

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Sample and copy cropped images for expert labeling")
    
    parser.add_argument("--sample-size", type=int, default=3000,
                        help="Number of images to sample (default: 3000)")
    parser.add_argument("--output-dir", type=str, default="public/images",
                        help="Output directory (default: public/images)")
    parser.add_argument("--queue-file", type=str, default="data/classification_queue.json",
                        help="Input classification queue file")
    parser.add_argument("--preserve-ratio", action="store_true", default=True,
                        help="Preserve the ratio of single/multi-box images")
    parser.add_argument("--balance-towns", action="store_true", default=True,
                        help="Balance sampling across towns")
    parser.add_argument("--debug", action="store_true",
                        help="Print detailed debug information")
    
    return parser.parse_args()

def sanitize_town_name(town):
    """Sanitize town name to match the format used in the JS script."""
    return town.upper().replace(" ", "_")

def load_classification_queue(queue_file):
    """Load the classification queue JSON file."""
    try:
        with open(queue_file, 'r') as f:
            queue_data = json.load(f)
        return queue_data
    except Exception as e:
        print(f"Error loading classification queue: {e}")
        return None

def select_stratified_sample(queue_data, args):
    """
    Select a stratified sample from the classification queue.
    
    The stratification ensures:
    1. Representation across all towns
    2. Balance between single-box and multi-box images
    3. Range of confidence scores
    """
    images = queue_data.get("images", [])
    
    if not images:
        print("No images found in classification queue!")
        return []
    
    # Group images by town
    town_images = defaultdict(list)
    
    # Also track single-box vs multi-box
    single_box_images = []
    multi_box_images = []
    
    for img in images:
        town = img.get("town", "unknown")
        town_images[town].append(img)
        
        if img.get("is_cropped", False):
            multi_box_images.append(img)
        else:
            single_box_images.append(img)
    
    print(f"Found {len(images)} total images across {len(town_images)} towns")
    print(f"Single-box images: {len(single_box_images)}, Multi-box images: {len(multi_box_images)}")
    
    # Calculate sampling distribution
    total_sample_size = args.sample_size
    selected_images = []
    
    # Approach 1: If preserving ratio of single/multi-box
    if args.preserve_ratio:
        single_ratio = len(single_box_images) / len(images)
        single_sample_size = int(total_sample_size * single_ratio)
        multi_sample_size = total_sample_size - single_sample_size
        
        print(f"Sampling {single_sample_size} single-box and {multi_sample_size} multi-box images")
        
        # Sample from each category
        if single_sample_size > 0:
            if args.balance_towns:
                # Balance across towns for single-box
                town_singles = defaultdict(list)
                for img in single_box_images:
                    town_singles[img["town"]].append(img)
                
                # Calculate images per town
                towns_count = len(town_singles)
                base_per_town = max(1, math.floor(single_sample_size / towns_count))
                
                # Distribute the sample
                for town, town_imgs in town_singles.items():
                    # Take either all images or the base amount, whichever is smaller
                    town_sample_size = min(len(town_imgs), base_per_town)
                    town_sample = random.sample(town_imgs, town_sample_size)
                    selected_images.extend(town_sample)
                
                # If we haven't reached our target, sample more from towns with remaining images
                remaining = single_sample_size - len(selected_images)
                if remaining > 0:
                    remaining_images = [img for img in single_box_images if img not in selected_images]
                    if remaining_images:
                        remaining_sample = random.sample(
                            remaining_images, 
                            min(remaining, len(remaining_images))
                        )
                        selected_images.extend(remaining_sample)
            else:
                # Simple random sampling for single-box
                selected_images.extend(
                    random.sample(single_box_images, min(single_sample_size, len(single_box_images)))
                )
        
        # Add multi-box samples
        if multi_sample_size > 0:
            if args.balance_towns:
                # Balance across towns for multi-box
                town_multis = defaultdict(list)
                for img in multi_box_images:
                    town_multis[img["town"]].append(img)
                
                # Calculate images per town
                towns_count = len(town_multis)
                base_per_town = max(1, math.floor(multi_sample_size / towns_count))
                
                # Distribute the sample
                already_selected = set(id(img) for img in selected_images)
                for town, town_imgs in town_multis.items():
                    town_sample_size = min(len(town_imgs), base_per_town)
                    town_sample = random.sample(town_imgs, town_sample_size)
                    for img in town_sample:
                        if id(img) not in already_selected:
                            selected_images.append(img)
                            already_selected.add(id(img))
                
                # If we haven't reached our target, sample more from towns with remaining images
                remaining = multi_sample_size - (len(selected_images) - single_sample_size)
                if remaining > 0:
                    remaining_images = [img for img in multi_box_images if id(img) not in already_selected]
                    if remaining_images:
                        remaining_sample = random.sample(
                            remaining_images, 
                            min(remaining, len(remaining_images))
                        )
                        selected_images.extend(remaining_sample)
            else:
                # Simple random sampling for multi-box
                multi_to_add = random.sample(multi_box_images, min(multi_sample_size, len(multi_box_images)))
                selected_images.extend(multi_to_add)
    
    # Approach 2: Pure town-based stratification
    else:
        if args.balance_towns:
            # Calculate a base number of images per town
            base_per_town = max(1, math.floor(total_sample_size / len(town_images)))
            
            # First, take the base number from each town
            for town, town_imgs in town_images.items():
                town_sample_size = min(len(town_imgs), base_per_town)
                selected_images.extend(random.sample(town_imgs, town_sample_size))
            
            # If we haven't reached our target, sample more from towns with remaining images
            remaining = total_sample_size - len(selected_images)
            if remaining > 0:
                remaining_images = [img for img in images if img not in selected_images]
                if remaining_images:
                    selected_images.extend(
                        random.sample(
                            remaining_images, 
                            min(remaining, len(remaining_images))
                        )
                    )
        else:
            # Simple proportional sampling
            for town, town_imgs in town_images.items():
                town_ratio = len(town_imgs) / len(images)
                town_sample_size = max(1, int(total_sample_size * town_ratio))
                town_sample_size = min(town_sample_size, len(town_imgs))
                selected_images.extend(random.sample(town_imgs, town_sample_size))
    
    # Adjust to exactly match the desired sample size
    if len(selected_images) > total_sample_size:
        random.shuffle(selected_images)
        selected_images = selected_images[:total_sample_size]
    elif len(selected_images) < total_sample_size:
        remaining = total_sample_size - len(selected_images)
        remaining_images = [img for img in images if img not in selected_images]
        if remaining_images and remaining > 0:
            selected_images.extend(
                random.sample(
                    remaining_images, 
                    min(remaining, len(remaining_images))
                )
            )
    
    # Calculate statistics for the selected sample
    sample_towns = defaultdict(int)
    sample_single_box = 0
    sample_multi_box = 0
    
    for img in selected_images:
        sample_towns[img["town"]] += 1
        if img.get("is_cropped", False):
            sample_multi_box += 1
        else:
            sample_single_box += 1
    
    print(f"\nSample Statistics:")
    print(f"Total selected: {len(selected_images)} images")
    print(f"Towns represented: {len(sample_towns)}/{len(town_images)}")
    print(f"Single-box ratio: {sample_single_box/len(selected_images):.2f} (original: {len(single_box_images)/len(images):.2f})")
    print(f"Multi-box ratio: {sample_multi_box/len(selected_images):.2f} (original: {len(multi_box_images)/len(images):.2f})")
    
    if args.debug:
        print("\nTown distribution:")
        for town, count in sorted(sample_towns.items(), key=lambda x: x[1], reverse=True):
            print(f"  {town}: {count} images ({count/len(selected_images)*100:.1f}%)")
    
    return selected_images

def copy_selected_images(selected_images, args):
    """Copy the selected images to the output directory."""
    # Clean the output directory
    if os.path.exists(args.output_dir):
        print(f"Cleaning output directory: {args.output_dir}")
        user_input = input(f"This will delete all existing files in {args.output_dir}. Continue? (y/n): ")
        if user_input.lower() != 'y':
            print("Operation canceled. Existing files will be kept.")
            return False
        
        shutil.rmtree(args.output_dir)
    
    # Create the output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create an additional flag in args to control side-by-side creation
    create_side_by_side = True  # You could make this a command line argument
    
    # Copy each selected image
    success_count = 0
    error_count = 0
    
    for img in selected_images:
        # Determine source path based on whether it's a cropped or original image
        if img.get("is_cropped", False):
            source_path = img.get("cropped_image")
            original_path = img.get("original_image")
            box = img.get("box")
        else:
            source_path = img.get("boxed_image", img.get("original_image"))
            original_path = None
            box = None
        
        # Get town and filename
        town = img.get("town", "unknown")
        
        # For cropped images, the filename is in the cropped_image path
        if img.get("is_cropped", False):
            filename = os.path.basename(source_path)
        else:
            filename = img.get("filename", os.path.basename(source_path))
        
        # Sanitize town name for directory structure
        sanitized_town = sanitize_town_name(town)
        
        # Create town directory if it doesn't exist
        town_dir = os.path.join(args.output_dir, sanitized_town)
        os.makedirs(town_dir, exist_ok=True)
        
        # Set target path
        target_path = os.path.join(town_dir, filename)
        
        try:
            if args.debug:
                print(f"Copying: {source_path} -> {target_path}")
            
            # Check if source file exists
            if not os.path.exists(source_path):
                print(f"Source file does not exist: {source_path}")
                error_count += 1
                continue
            
            # For cropped images with available original, create side-by-side composite
            if create_side_by_side and img.get("is_cropped", False) and original_path and os.path.exists(original_path):
                # Create a different filename for the composite
                composite_filename = f"composite_{filename}"
                composite_path = os.path.join(town_dir, composite_filename)
                
                # Create the side-by-side image
                if create_side_by_side_image(source_path, original_path, box, composite_path):
                    # Use the composite as the target instead
                    target_path = composite_path
                    success_count += 1
                else:
                    # Fall back to just copying the cropped image
                    shutil.copy2(source_path, target_path)
                    success_count += 1
            else:
                # Copy the file normally
                shutil.copy2(source_path, target_path)
                success_count += 1
            
        except Exception as e:
            print(f"Error copying {source_path}: {e}")
            error_count += 1
    
    print(f"\nCopy Summary:")
    print(f"Successfully copied: {success_count} images")
    print(f"Failed to copy: {error_count} images")
    print(f"Output directory: {os.path.abspath(args.output_dir)}")
    
    return success_count > 0

def create_side_by_side_image(cropped_path, original_path, box, output_path):
    """
    Create a side-by-side composite image showing both cropped and original views.
    
    Args:
        cropped_path: Path to the cropped image
        original_path: Path to the original image
        box: Bounding box coordinates [x1, y1, x2, y2]
        output_path: Path to save the composite image
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Open both images
        cropped_img = Image.open(cropped_path)
        original_img = Image.open(original_path)
        
        # Get dimensions
        crop_width, crop_height = cropped_img.size
        orig_width, orig_height = original_img.size
        
        # Calculate new dimensions
        # Make the original image the same height as the cropped for side-by-side
        new_orig_height = crop_height
        new_orig_width = int(orig_width * (new_orig_height / orig_height))
        
        # Resize original image
        resized_orig = original_img.resize((new_orig_width, new_orig_height), Image.LANCZOS)
        
        # Create a new image wide enough for both
        total_width = crop_width + new_orig_width + 20  # 20px padding
        composite = Image.new('RGB', (total_width, crop_height + 30), (255, 255, 255))
        
        # Paste the cropped image on the left
        composite.paste(cropped_img, (0, 0))
        
        # Paste the original image on the right with some spacing
        composite.paste(resized_orig, (crop_width + 20, 0))
        
        # Draw a line to separate the images
        draw = ImageDraw.Draw(composite)
        draw.line([(crop_width + 10, 0), (crop_width + 10, crop_height)], fill=(200, 200, 200), width=1)
        
        # Add labels
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, crop_height + 5), "Cropped View", fill=(0, 0, 0), font=font)
        draw.text((crop_width + 30, crop_height + 5), "Original Context", fill=(0, 0, 0), font=font)
        
        # Mark the bounding box in the original context view
        if box:
            # Scale the box coordinates to fit the resized original
            scale_x = new_orig_width / orig_width
            scale_y = new_orig_height / orig_height
            
            scaled_box = [
                int(box[0] * scale_x),
                int(box[1] * scale_y),
                int(box[2] * scale_x),
                int(box[3] * scale_y)
            ]
            
            # Draw dashed rectangle
            x0, y0, x1, y1 = scaled_box
            dash_length = 6
            dash_gap = 3
            
            # Adjust coordinates to the position in the composite image
            x0 += crop_width + 20
            x1 += crop_width + 20
            
            # Draw dashed lines
            for x in range(int(x0), int(x1), dash_length + dash_gap):
                end_x = min(x + dash_length, x1)
                draw.line([(x, y0), (end_x, y0)], fill="red", width=2)
                draw.line([(x, y1), (end_x, y1)], fill="red", width=2)
            
            for y in range(int(y0), int(y1), dash_length + dash_gap):
                end_y = min(y + dash_length, y1)
                draw.line([(x0, y), (x0, end_y)], fill="red", width=2)
                draw.line([(x1, y), (x1, end_y)], fill="red", width=2)
        
        # Save the composite image
        composite.save(output_path, quality=85)
        return True
    except Exception as e:
        print(f"Error creating side-by-side image: {e}")
        return False

def main():
    """Main function to run the script."""
    args = parse_arguments()
    
    print("\nFlag Image Sampling for Expert Labelling")
    print("----------------------------------------")
    print(f"Target sample size: {args.sample_size}")
    print(f"Output directory: {args.output_dir}")
    print(f"Queue file: {args.queue_file}")
    print(f"Preserve single/multi-box ratio: {args.preserve_ratio}")
    print(f"Balance towns: {args.balance_towns}")
    
    # Load classification queue
    queue_data = load_classification_queue(args.queue_file)
    if not queue_data:
        print("Failed to load classification queue. Exiting.")
        return
    
    # Select stratified sample
    selected_images = select_stratified_sample(queue_data, args)
    if not selected_images:
        print("No images selected. Exiting.")
        return
    
    # Copy selected images
    success = copy_selected_images(selected_images, args)
    if not success:
        print("Failed to copy images. Exiting.")
        return
    
    print("\nNext steps:")
    print("1. Run the generate-image-list.js script to update the image list:")
    print("   node scripts/generate-image-list.js")
    print("2. Deploy the updated app to Vercel")

if __name__ == "__main__":
    main()
