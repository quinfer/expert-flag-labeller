#!/usr/bin/env python3
"""
Flag Image Preprocessing Script for Classification

This script processes images with multiple bounding boxes to create single-box images
suitable for classification in the Next.js app. It handles distant flags appropriately
by using relative size and position-aware filtering.

Usage:
    python prepare_images_for_classification.py [options]

Options:
    --min-confidence FLOAT   Minimum confidence score threshold (default: 0.3)
    --min-size FLOAT         Minimum relative size as percentage of image (default: 0.005)
    --output-dir DIR         Output directory for cropped images (default: data/cropped_images_for_classification)
    --queue-file FILE        Output JSON file path (default: data/classification_queue.json)
    --random-sample INT      Randomly sample N images from each town (default: process all)
    --max-per-town INT       Maximum number of images to process per town (default: no limit)
    --auto-threshold         Automatically adjust thresholds based on image analysis
    --highlight              Highlight the bounding box in the cropped image (default: True)
    --line-width INT         Width of bounding box line (default: 1)
    --dashed                 Use dashed lines for bounding boxes
    --show-confidence        Show confidence scores on bounding boxes
    --stats                  Show detailed statistics about the dataset
    --debug                  Enable debug output
    --no-clean               Skip cleaning the output directory
    --web-path               Web-accessible base path for images in JSON (default: /images)
    --copy-to-public         Copy processed images to the public directory
    --public-dir             Public directory for web-accessible images (default: public/images)
    --side-by-side           Create side-by-side versions of cropped and original images
"""

import os
import json
import argparse
import random
from collections import Counter, defaultdict
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from datetime import datetime
import shutil

# Base directories
BASE_DIR = "data"
TRUE_POSITIVE_DIR = os.path.join(BASE_DIR, "true_positive_images")
OUTPUT_DIR = os.path.join(BASE_DIR, "cropped_images_for_classification")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Prepare images for flag classification")
    
    parser.add_argument("--min-confidence", type=float, default=0.3,
                        help="Minimum confidence score (default: 0.3)")
    parser.add_argument("--min-size", type=float, default=0.005,
                        help="Minimum relative size as fraction of image area (default: 0.005 = 0.5%%)")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR,
                        help=f"Output directory for cropped images (default: {OUTPUT_DIR})")
    parser.add_argument("--queue-file", type=str, default=os.path.join(BASE_DIR, "classification_queue.json"),
                        help="Output JSON file path")
    parser.add_argument("--random-sample", type=int,
                        help="Randomly sample N images from each town")
    parser.add_argument("--max-per-town", type=int,
                        help="Maximum number of images to process per town")
    parser.add_argument("--auto-threshold", action="store_true",
                        help="Automatically adjust thresholds based on image analysis")
    parser.add_argument("--highlight", action="store_true", default=True,
                        help="Highlight the bounding box in the cropped image")
    parser.add_argument("--line-width", type=int, default=1,
                        help="Width of bounding box line (default: 1)")
    parser.add_argument("--dashed", action="store_true", default=True,
                        help="Use dashed lines for bounding boxes")
    parser.add_argument("--show-confidence", action="store_true", default=True,
                        help="Show confidence scores on bounding boxes")
    parser.add_argument("--stats", action="store_true",
                        help="Show detailed statistics about the dataset")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug output")
    parser.add_argument("--no-clean", action="store_true",
                        help="Skip cleaning the output directory")
    parser.add_argument("--auto-clean", action="store_true",
                        help="Automatically clean the output directory without confirmation")
    parser.add_argument("--web-path", type=str, default="/images",
                        help="Web-accessible base path for images in JSON (default: /images)")
    parser.add_argument("--copy-to-public", action="store_true",
                        help="Copy processed images to the public directory")
    parser.add_argument("--public-dir", type=str, default="public/images",
                        help="Public directory for web-accessible images (default: public/images)")
    parser.add_argument("--side-by-side", action="store_true",
                        help="Create side-by-side versions of cropped and original images")
    
    return parser.parse_args()

def analyze_dataset():
    """Analyze the dataset to gather statistics."""
    towns = [d for d in os.listdir(TRUE_POSITIVE_DIR) 
             if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, d))]
    
    stats = {
        "total_images": 0,
        "total_boxes": 0,
        "box_count_distribution": Counter(),
        "confidence_distribution": defaultdict(list),
        "size_distribution": defaultdict(list),
        "position_distribution": defaultdict(list),
        "town_stats": {}
    }
    
    for town in towns:
        town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
        bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
        town_stats = {
            "images": 0,
            "boxes": 0,
            "avg_confidence": 0,
            "single_box_images": 0,
            "multi_box_images": 0
        }
        
        try:
            with open(bbox_file, 'r') as f:
                bbox_data = json.load(f)
            
            town_stats["images"] = len(bbox_data)
            stats["total_images"] += len(bbox_data)
            
            confidences = []
            for image_name, detections in bbox_data.items():
                box_count = len(detections)
                town_stats["boxes"] += box_count
                stats["total_boxes"] += box_count
                stats["box_count_distribution"][box_count] += 1
                
                if box_count == 1:
                    town_stats["single_box_images"] += 1
                else:
                    town_stats["multi_box_images"] += 1
                
                image_path = os.path.join(town_dir, image_name)
                if os.path.exists(image_path):
                    try:
                        image = Image.open(image_path)
                        img_width, img_height = image.size
                        total_image_area = img_width * img_height
                        
                        for detection in detections:
                            confidence = detection["confidence"]
                            confidences.append(confidence)
                            
                            box = detection["box"]
                            box_width = box[2] - box[0]
                            box_height = box[3] - box[1]
                            box_area = box_width * box_height
                            relative_size = box_area / total_image_area
                            
                            y_center = (box[1] + box[3]) / 2
                            position_factor = 1 - (y_center / img_height)
                            
                            # Round to nearest 0.1 for binning
                            conf_bin = round(confidence * 10) / 10
                            size_bin = round(relative_size * 100) / 100
                            pos_bin = round(position_factor * 10) / 10
                            
                            stats["confidence_distribution"][conf_bin].append(confidence)
                            stats["size_distribution"][size_bin].append(relative_size)
                            stats["position_distribution"][pos_bin].append(position_factor)
                            
                    except Exception as e:
                        print(f"Error analyzing image {image_path}: {e}")
            
            if confidences:
                town_stats["avg_confidence"] = sum(confidences) / len(confidences)
        
        except Exception as e:
            print(f"Error analyzing town {town}: {e}")
        
        stats["town_stats"][town] = town_stats
    
    return stats

def auto_determine_thresholds(stats):
    """Automatically determine optimal thresholds based on dataset analysis."""
    # Get confidence distribution
    all_confidences = []
    for conf_list in stats["confidence_distribution"].values():
        all_confidences.extend(conf_list)
    
    # Get size distribution
    all_sizes = []
    for size_list in stats["size_distribution"].values():
        all_sizes.extend(size_list)
    
    # Calculate thresholds at the 10th percentile
    if all_confidences:
        confidence_threshold = max(0.2, np.percentile(all_confidences, 10))
    else:
        confidence_threshold = 0.3
    
    if all_sizes:
        size_threshold = max(0.001, np.percentile(all_sizes, 5))
    else:
        size_threshold = 0.005
    
    return confidence_threshold, size_threshold

def print_dataset_statistics(stats):
    """Print detailed statistics about the dataset."""
    print("\n" + "="*80)
    print("DATASET STATISTICS".center(80))
    print("="*80)
    
    print(f"\nTotal Images: {stats['total_images']}")
    print(f"Total Bounding Boxes: {stats['total_boxes']}")
    print(f"Average Boxes per Image: {stats['total_boxes'] / stats['total_images']:.2f}")
    
    print("\nBounding Box Count Distribution:")
    for count, frequency in sorted(stats["box_count_distribution"].items()):
        percentage = (frequency / stats['total_images']) * 100
        print(f"  {count} boxes: {frequency} images ({percentage:.1f}%)")
    
    print("\nBounding Box Size Distribution (as % of image area):")
    size_bins = sorted(stats["size_distribution"].keys())
    for size_bin in size_bins:
        count = len(stats["size_distribution"][size_bin])
        percentage = (count / stats['total_boxes']) * 100
        print(f"  {size_bin*100:.1f}%: {count} boxes ({percentage:.1f}%)")
    
    print("\nBounding Box Position Distribution (0=bottom, 1=top):")
    pos_bins = sorted(stats["position_distribution"].keys())
    for pos_bin in pos_bins:
        count = len(stats["position_distribution"][pos_bin])
        percentage = (count / stats['total_boxes']) * 100
        print(f"  {pos_bin:.1f}: {count} boxes ({percentage:.1f}%)")
    
    print("\nConfidence Score Distribution:")
    conf_bins = sorted(stats["confidence_distribution"].keys())
    for conf_bin in conf_bins:
        count = len(stats["confidence_distribution"][conf_bin])
        percentage = (count / stats['total_boxes']) * 100
        print(f"  {conf_bin:.1f}: {count} boxes ({percentage:.1f}%)")
    
    print("\nStatistics by Town:")
    for town, town_stats in sorted(stats["town_stats"].items()):
        print(f"\n  {town}:")
        print(f"    Images: {town_stats['images']}")
        print(f"    Boxes: {town_stats['boxes']}")
        print(f"    Avg Confidence: {town_stats['avg_confidence']:.2f}")
        print(f"    Single-box Images: {town_stats['single_box_images']} "
              f"({town_stats['single_box_images']/town_stats['images']*100:.1f}%)")
        print(f"    Multi-box Images: {town_stats['multi_box_images']} "
              f"({town_stats['multi_box_images']/town_stats['images']*100:.1f}%)")
    
    print("\n" + "="*80 + "\n")

def clean_output_directory(output_dir):
    """
    Remove all existing cropped images from the output directory.
    
    Args:
        output_dir: Path to the output directory
    """
    print(f"Cleaning output directory: {output_dir}")
    
    # Access the global args variable
    global args
    
    if os.path.exists(output_dir):
        # Skip confirmation if --auto-clean is provided
        if hasattr(args, 'auto_clean') and args.auto_clean:
            confirm = True
        else:
            # Ask for confirmation before deletion
            try:
                user_input = input(f"This will delete all existing files in {output_dir}. Continue? (y/n): ")
                confirm = user_input.lower() == 'y'
            except EOFError:
                # Handle EOF (e.g., when running in a script)
                print("Auto-confirming due to non-interactive environment")
                confirm = True
                
        if not confirm:
            print("Operation canceled. Existing files will be kept.")
            return
        
        # First try to remove the entire directory and its contents
        try:
            shutil.rmtree(output_dir)
            print(f"Removed all contents from {output_dir}")
        except Exception as e:
            print(f"Warning: Could not completely remove directory: {e}")
            
            # If that fails, try to remove files individually
            try:
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if file.endswith('.jpg') or file.endswith('.png'):
                            os.remove(os.path.join(root, file))
                            if args.debug:
                                print(f"Removed file: {os.path.join(root, file)}")
            except Exception as e2:
                print(f"Warning: Could not remove all files: {e2}")
    
    # Create a fresh directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created fresh output directory: {output_dir}")

def prepare_images_for_classification(args):
    """
    Process multi-box images to create single-box images for classification.
    
    Args:
        args: Command line arguments parsed by argparse
        
    Returns:
        List of image paths ready for classification
    """
    # Clean the output directory first (unless --no-clean is specified)
    if not args.no_clean:
        clean_output_directory(args.output_dir)
    
    # Get all towns
    towns = [d for d in os.listdir(TRUE_POSITIVE_DIR) 
            if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, d))]
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    classification_queue = []
    processed_counts = {town: 0 for town in towns}
    total_boxes_processed = 0
    
    # If auto-threshold is enabled, analyze the dataset first
    if args.auto_threshold or args.stats:
        print("Analyzing dataset statistics...")
        stats = analyze_dataset()
        
        if args.stats:
            print_dataset_statistics(stats)
        
        if args.auto_threshold:
            confidence_threshold, size_threshold = auto_determine_thresholds(stats)
            print(f"Auto-determined thresholds: confidence={confidence_threshold:.2f}, size={size_threshold:.5f}")
            args.min_confidence = confidence_threshold
            args.min_size = size_threshold
    
    print(f"Processing images with min_confidence={args.min_confidence} and min_size={args.min_size}...")
    
    # Process each town
    for town in towns:
        town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
        bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
        
        try:
            with open(bbox_file, 'r') as f:
                bbox_data = json.load(f)
            
            # If random sampling is enabled, randomly select images
            image_names = list(bbox_data.keys())
            
            # TEMPORARY DEBUG: Force include the specific test image
            # Check if the specific problem image exists in this town
            specific_test_image = "1AmokbVfS_LJwaLjwWeXwQ_120.jpg"
            if town == "ANTRIM" and specific_test_image in image_names:
                print(f"Found specific test image in {town}: {specific_test_image}")
                # Remove it first to avoid duplication
                if specific_test_image in image_names:
                    image_names.remove(specific_test_image)
                    
            if args.random_sample and args.random_sample < len(image_names):
                random.shuffle(image_names)
                image_names = image_names[:args.random_sample]
                
                # Add the specific test image if it exists in this town
                if town == "ANTRIM" and specific_test_image in bbox_data:
                    print(f"Adding specific test image to the selection: {specific_test_image}")
                    image_names.insert(0, specific_test_image)
            
            # Process each image
            for image_name in image_names:
                # Check if we've reached the max per town limit
                if args.max_per_town and processed_counts[town] >= args.max_per_town:
                    break
                
                detections = bbox_data[image_name]
                image_path = os.path.join(town_dir, image_name)
                
                # For single-box images, draw bounding box on the original image
                if len(detections) == 1:
                    try:
                        # Draw box on the image
                        boxed_path = draw_boxes_on_image(image_path, detections, args)
                        
                        # Copy to public directory if requested
                        web_path = copy_to_public_dir(boxed_path, town, args)
                        original_web_path = copy_to_public_dir(image_path, town, args)
                        
                        # Add to classification queue
                        classification_queue.append({
                            'town': town,
                            'original_image': original_web_path,
                            'boxed_image': web_path,
                            'filename': os.path.basename(boxed_path),
                            'box_index': 0,
                            'confidence': detections[0]['confidence'],
                            'box': detections[0]['box'],
                            'is_cropped': False,
                            'has_box_drawn': True,
                            'distance_hint': 'Single detection'
                        })
                        
                        processed_counts[town] += 1
                        total_boxes_processed += 1
                        
                        if args.debug:
                            print(f"Added single-box image: {boxed_path}")
                        
                    except Exception as e:
                        print(f"Error processing single-box image {image_path}: {e}")
                        # Fallback to original approach if processing fails
                        web_path = copy_to_public_dir(image_path, town, args)
                        classification_queue.append({
                            'town': town,
                            'original_image': web_path,
                            'filename': image_name,
                            'box_index': 0,
                            'confidence': detections[0]['confidence'],
                            'box': detections[0]['box'],
                            'is_cropped': False,
                            'has_box_drawn': False,
                            'distance_hint': 'Single detection'
                        })
                        
                        processed_counts[town] += 1
                        total_boxes_processed += 1
                    
                    continue
                
                # For multi-box images, process each box
                try:
                    image = Image.open(image_path)
                    img_width, img_height = image.size
                    total_image_area = img_width * img_height
                    
                    # Create town subdirectory in the output dir
                    town_output_dir = os.path.join(args.output_dir, town)
                    os.makedirs(town_output_dir, exist_ok=True)
                    
                    boxes_added = 0
                    
                    for i, detection in enumerate(detections):
                        box = detection['box']
                        confidence = detection['confidence']
                        
                        # Calculate relative box size
                        box_width = box[2] - box[0]
                        box_height = box[3] - box[1]
                        box_area = box_width * box_height
                        relative_size = box_area / total_image_area
                        
                        # Calculate position factor (0-1, higher means likely more distant)
                        # Flags at the top of the image are often far away
                        y_center = (box[1] + box[3]) / 2
                        position_factor = 1 - (y_center / img_height)  # 0 at bottom, 1 at top
                        
                        # Calculate a combined score that favors:
                        # - Higher confidence
                        # - Larger relative size
                        # - Adjusts for position (distance)
                        position_adjustment = 1 + (position_factor * 0.5)  # 1.0-1.5x multiplier for height
                        adjusted_size = relative_size * position_adjustment
                        
                        # Determine distance hint
                        if relative_size < 0.01:
                            if position_factor > 0.7:
                                distance_hint = "Likely distant flag (high in image)"
                            else:
                                distance_hint = "Small detection - possibly distant flag"
                        else:
                            distance_hint = "Normal sized detection"
                        
                        # More lenient filtering for boxes high in the image (distant flags)
                        min_size_threshold = args.min_size
                        if position_factor > 0.7:  # If in top 30% of image
                            min_size_threshold = args.min_size * 0.5  # 50% more lenient
                        
                        # Skip low confidence or extremely small boxes that aren't high in the image
                        if confidence < args.min_confidence or adjusted_size < min_size_threshold:
                            if args.debug:
                                print(f"Skipping box {i} in {image_path}: confidence={confidence:.2f}, size={relative_size:.5f}, position={position_factor:.2f}")
                            continue
                        
                        # Create a cropped image with padding
                        # Use larger padding for small boxes to provide more context
                        base_padding = 50
                        size_factor = max(0.5, min(1.5, 0.05 / relative_size))  # More padding for small boxes
                        padding = int(base_padding * size_factor)
                        
                        crop_box = [
                            max(0, box[0] - padding),
                            max(0, box[1] - padding),
                            min(img_width, box[2] + padding),
                            min(img_height, box[3] + padding)
                        ]
                        
                        cropped_img = image.crop(crop_box)
                        
                        # Draw rectangle on the cropped image to highlight the box if requested
                        if args.highlight:
                            draw = ImageDraw.Draw(cropped_img)
                            relative_box = [
                                box[0] - crop_box[0],
                                box[1] - crop_box[1],
                                box[2] - crop_box[0],
                                box[3] - crop_box[1]
                            ]
                            
                            # Get width from args
                            line_width = args.line_width
                            
                            if args.dashed:
                                # Create dashed line
                                dash_length = 6  # Length of each dash
                                dash_gap = 3     # Gap between dashes
                                
                                # Draw dashed rectangle with specified line width
                                x0, y0, x1, y1 = relative_box
                                
                                # Draw horizontal dashed lines (top and bottom)
                                for x in range(int(x0), int(x1), dash_length + dash_gap):
                                    # Top line
                                    end_x = min(x + dash_length, x1)
                                    draw.line([(x, y0), (end_x, y0)], fill="red", width=line_width)
                                    # Bottom line
                                    draw.line([(x, y1), (end_x, y1)], fill="red", width=line_width)
                                
                                # Draw vertical dashed lines (left and right)
                                for y in range(int(y0), int(y1), dash_length + dash_gap):
                                    # Left line
                                    end_y = min(y + dash_length, y1)
                                    draw.line([(x0, y), (x0, end_y)], fill="red", width=line_width)
                                    # Right line
                                    draw.line([(x1, y), (x1, end_y)], fill="red", width=line_width)
                            else:
                                # Draw solid rectangle
                                draw.rectangle(relative_box, outline="red", width=line_width)
                        # Add confidence score text if requested
                        if args.show_confidence:
                            # Choose font size based on image size
                            box_width = relative_box[2] - relative_box[0]
                            box_height = relative_box[3] - relative_box[1]
                            font_size = max(10, int(min(box_width, box_height) / 15))
                            
                            try:
                                from PIL import ImageFont
                                font = ImageFont.truetype("arial.ttf", font_size)
                            except Exception:
                                # Fallback for systems without arial
                                font = None
                            
                            # Format confidence as percentage
                            conf_text = f"{confidence:.0%}"
                            
                            # Position text ABOVE the top-left corner of box
                            text_x = relative_box[0] + 3
                            text_y = relative_box[1] - font_size - 5  # Position above the box instead of inside
                            
                            # Ensure text doesn't go off the top of the image
                            if text_y < 0:
                                # If no space above, place it below the bottom-left corner instead
                                text_y = relative_box[3] + 5
                            
                            # Draw text with background for better visibility
                            try:
                                text_width, text_height = draw.textsize(conf_text, font=font) if font else (len(conf_text) * font_size // 2, font_size)
                            except AttributeError:
                                # For newer Pillow versions
                                if font:
                                    text_width, text_height = font.getbbox(conf_text)[2:]
                                else:
                                    text_width, text_height = (len(conf_text) * font_size // 2, font_size)
                                    
                            draw.rectangle(
                                [(text_x - 1, text_y - 1), (text_x + text_width + 1, text_y + text_height + 1)], 
                                fill="white"
                            )
                            draw.text((text_x, text_y), conf_text, fill="red", font=font)
                        
                        # Save cropped image
                        crop_filename = f"{image_name.split('.')[0]}_box{i}.jpg"
                        crop_path = os.path.join(town_output_dir, crop_filename)
                        cropped_img.save(crop_path)
                        
                        # Copy to public directory
                        cropped_web_path = copy_to_public_dir(crop_path, town, args)
                        
                        # Create side-by-side view if requested
                        composite_web_path = None
                        if args.side_by_side:
                            composite_filename = f"composite_{image_name.split('.')[0]}_box{i}.jpg"
                            composite_path = os.path.join(town_output_dir, composite_filename)
                            
                            if create_side_by_side_image(crop_path, image_path, box, composite_path):
                                composite_web_path = copy_to_public_dir(composite_path, town, args)
                        
                        # Add to classification queue
                        item = {
                            'town': town,
                            'original_image': cropped_web_path,
                            'cropped_image': cropped_web_path,
                            'filename': crop_filename,
                            'box_index': i,
                            'confidence': confidence,
                            'relative_size': float(relative_size),
                            'position_factor': float(position_factor),
                            'box': box,
                            'is_cropped': True,
                            'has_box_drawn': True,
                            'distance_hint': distance_hint
                        }
                        
                        # Add the composite image path if it was created
                        if composite_web_path:
                            item['composite_image'] = composite_web_path
                            item['has_composite'] = True
                        
                        classification_queue.append(item)
                        
                        boxes_added += 1
                        total_boxes_processed += 1
                        
                        if args.debug:
                            print(f"Added box {i} from {image_path}: confidence={confidence:.2f}, size={relative_size:.5f}, position={position_factor:.2f}")
                    
                    if boxes_added > 0:
                        processed_counts[town] += 1
                
                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
        
        except Exception as e:
            print(f"Error scanning {town}: {e}")
    
    # Sort the queue by a composite score (confidence + size factor)
    classification_queue.sort(key=lambda x: (x['confidence'] * 0.7 + 
                                           (x.get('relative_size', 0.1) * 30)), 
                             reverse=True)
    
    # Save the queue to a JSON file for the Next.js app
    with open(args.queue_file, 'w') as f:
        json.dump({
            "metadata": {
                "created": datetime.now().isoformat(),
                "min_confidence": args.min_confidence,
                "min_size": args.min_size,
                "total_images": sum(processed_counts.values()),
                "total_boxes": total_boxes_processed
            },
            "images": classification_queue
        }, f, indent=2)
    
    print(f"\nSummary:")
    print(f"- Created classification queue with {len(classification_queue)} boxes")
    print(f"- Processed {sum(processed_counts.values())} images across {len(towns)} towns")
    print(f"- Output JSON saved to: {args.queue_file}")
    print(f"- Cropped images saved to: {args.output_dir}")
    
    return classification_queue

def draw_boxes_on_image(image_path, detections, args):
    """
    Draw bounding boxes on an image.
    """
    try:
        # Open the image
        image = Image.open(image_path)
        modified_img = image.copy()
        draw = ImageDraw.Draw(modified_img)
        
        for detection in detections:
            box = detection['box']
            confidence = detection['confidence']
            
            # Draw rectangle (dashed or solid)
            if args.dashed:
                # Create dashed line
                dash_length = 6  # Length of each dash
                dash_gap = 3     # Gap between dashes
                
                # Draw dashed rectangle
                x0, y0, x1, y1 = box
                
                # Draw horizontal dashed lines (top and bottom)
                for x in range(int(x0), int(x1), dash_length + dash_gap):
                    # Top line
                    end_x = min(x + dash_length, x1)
                    draw.line([(x, y0), (end_x, y0)], fill="red", width=args.line_width)
                    # Bottom line
                    draw.line([(x, y1), (end_x, y1)], fill="red", width=args.line_width)
                
                # Draw vertical dashed lines (left and right)
                for y in range(int(y0), int(y1), dash_length + dash_gap):
                    # Left line
                    end_y = min(y + dash_length, y1)
                    draw.line([(x0, y), (x0, end_y)], fill="red", width=args.line_width)
                    # Right line
                    draw.line([(x1, y), (x1, end_y)], fill="red", width=args.line_width)
            else:
                # Draw solid rectangle
                draw.rectangle(box, outline="red", width=args.line_width)
            
            # Add confidence score text if requested
            if args.show_confidence:
                # Choose font size based on image size
                box_width = box[2] - box[0]
                box_height = box[3] - box[1]
                font_size = max(10, int(min(box_width, box_height) / 15))
                
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except Exception:
                    # Fallback for systems without arial
                    font = None
                
                # Format confidence as percentage
                conf_text = f"{confidence:.0%}"
                
                # Position text ABOVE the top-left corner of box
                text_x = box[0] + 3
                text_y = box[1] - font_size - 5  # Position above the box
                
                # Ensure text doesn't go off the top of the image
                if text_y < 0:
                    # If no space above, place it below the bottom-left corner
                    text_y = box[3] + 5
                
                # Draw text with background
                try:
                    text_width, text_height = draw.textsize(conf_text, font=font) if font else (len(conf_text) * font_size // 2, font_size)
                except AttributeError:
                    # For newer Pillow versions
                    if font:
                        text_width, text_height = font.getbbox(conf_text)[2:]
                    else:
                        text_width, text_height = (len(conf_text) * font_size // 2, font_size)
                        
                draw.rectangle(
                    [(text_x - 1, text_y - 1), (text_x + text_width + 1, text_y + text_height + 1)], 
                    fill="white"
                )
                draw.text((text_x, text_y), conf_text, fill="red", font=font)
        
        # Generate a new filename
        base_name = os.path.basename(image_path)
        name_parts = os.path.splitext(base_name)
        boxed_filename = f"{name_parts[0]}_boxed{name_parts[1]}"
        
        # Create the output directory if it doesn't exist
        output_dir = os.path.dirname(image_path)
        boxed_path = os.path.join(output_dir, boxed_filename)
        
        # Save the modified image
        modified_img.save(boxed_path)
        return boxed_path
        
    except Exception as e:
        print(f"Error drawing boxes on {image_path}: {e}")
        raise

def copy_to_public_dir(source_path, town, args):
    """
    Copy an image to the public directory for web access.
    """
    if not args.copy_to_public:
        return source_path
        
    try:
        # Create town subdirectory in public dir
        sanitized_town = town.upper().replace(" ", "_")
        town_public_dir = os.path.join(args.public_dir, sanitized_town)
        os.makedirs(town_public_dir, exist_ok=True)
        
        # Get filename and create destination path
        filename = os.path.basename(source_path)
        dest_path = os.path.join(town_public_dir, filename)
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        
        # Return web-accessible path
        return f"{args.web_path}/{sanitized_town}/{filename}"
        
    except Exception as e:
        print(f"Error copying to public dir: {e}")
        return source_path

def create_side_by_side_image(cropped_path, original_path, box, output_path):
    """
    Create a side-by-side composite image showing both cropped and original views.
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
    global args
    args = parse_arguments()
    
    print("\nFlag Image Preprocessing for Classification")
    print("-------------------------------------------")
    print(f"Min confidence: {args.min_confidence}")
    print(f"Min relative size: {args.min_size} (0.5% of image area)")
    print(f"Output directory: {args.output_dir}")
    print(f"Queue file: {args.queue_file}")
    
    if args.random_sample:
        print(f"Random sampling: {args.random_sample} images per town")
    
    if args.max_per_town:
        print(f"Max per town: {args.max_per_town} images")
    
    if args.auto_threshold:
        print("Auto threshold: Enabled")
        
    if args.side_by_side:
        print("Side-by-side mode: Enabled")
        
    if args.auto_clean:
        print("Auto clean: Enabled (will clean without confirmation)")
    
    start_time = datetime.now()
    classification_queue = prepare_images_for_classification(args)
    end_time = datetime.now()
    
    print(f"\nProcessing completed in {(end_time - start_time).total_seconds():.1f} seconds")
    print(f"Generated {len(classification_queue)} images for classification")

if __name__ == "__main__":
    main() 