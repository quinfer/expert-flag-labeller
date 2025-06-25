#!/usr/bin/env python3
"""
Generate visualizations of extreme cases for methodology documentation.

This script identifies images with the largest number of bounding boxes,
creates visualizations with dashed lines and confidence scores, and
saves them in a format suitable for academic documentation.

Usage:
    python generate_example_visualizations.py --num-examples 5 --output-dir figures
"""

import os
import json
import argparse
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Base directories (same as in prepare_images_for_classification.py)
BASE_DIR = "data"
TRUE_POSITIVE_DIR = os.path.join(BASE_DIR, "true_positive_images")
OUTPUT_DIR = os.path.join(BASE_DIR, "example_figures")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate example visualizations")
    parser.add_argument("--num-examples", type=int, default=5,
                        help="Number of extreme examples to visualize")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR,
                        help="Output directory for figures")
    parser.add_argument("--dpi", type=int, default=300,
                        help="DPI for output figures")
    parser.add_argument("--include-cropped", action="store_true", default=True,
                        help="Include cropped versions of selected boxes")
    return parser.parse_args()

def find_extreme_examples(num_examples=5):
    """Find images with the largest number of bounding boxes."""
    towns = [d for d in os.listdir(TRUE_POSITIVE_DIR) 
             if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, d))]
    
    # Collect all images with their box counts
    all_images = []
    
    for town in towns:
        town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
        bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
        
        try:
            with open(bbox_file, 'r') as f:
                bbox_data = json.load(f)
            
            for image_name, detections in bbox_data.items():
                box_count = len(detections)
                if box_count > 10:  # Only consider images with many boxes
                    image_path = os.path.join(town_dir, image_name)
                    if os.path.exists(image_path):
                        all_images.append({
                            'town': town,
                            'image_name': image_name,
                            'path': image_path,
                            'box_count': box_count,
                            'detections': detections
                        })
        except Exception as e:
            print(f"Error scanning {town}: {e}")
    
    # Sort by box count (descending) and get the top examples
    all_images.sort(key=lambda x: x['box_count'], reverse=True)
    return all_images[:num_examples]

def draw_boxes_with_confidence(image, detections, line_width=1):
    """Draw bounding boxes with dashed lines and confidence scores."""
    draw = ImageDraw.Draw(image)
    
    try:
        # Try to load a font
        font = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
    
    for detection in detections:
        box = detection['box']
        confidence = detection['confidence']
        
        # Draw dashed rectangle
        dash_length = 6  # Length of each dash
        dash_gap = 3     # Gap between dashes
        
        x0, y0, x1, y1 = box
        
        # Draw horizontal dashed lines (top and bottom)
        for x in range(int(x0), int(x1), dash_length + dash_gap):
            end_x = min(x + dash_length, x1)
            draw.line([(x, y0), (end_x, y0)], fill="red", width=line_width)
            draw.line([(x, y1), (end_x, y1)], fill="red", width=line_width)
        
        # Draw vertical dashed lines (left and right)
        for y in range(int(y0), int(y1), dash_length + dash_gap):
            end_y = min(y + dash_length, y1)
            draw.line([(x0, y), (x0, end_y)], fill="red", width=line_width)
            draw.line([(x1, y), (x1, end_y)], fill="red", width=line_width)
        
        # Format confidence as percentage
        conf_text = f"{confidence:.0%}"
        
        # Position text at top-left corner of box with slight offset
        text_x = x0 + 3
        text_y = y0 + 3
        
        # Draw text with background for better visibility
        try:
            text_width, text_height = draw.textsize(conf_text, font=font)
        except AttributeError:
            # For newer Pillow versions
            if hasattr(font, "getbbox"):
                text_width, text_height = font.getbbox(conf_text)[2:]
            else:
                text_width, text_height = (len(conf_text) * 8, 14)
                
        draw.rectangle(
            [(text_x - 1, text_y - 1), (text_x + text_width + 1, text_y + text_height + 1)], 
            fill="white"
        )
        draw.text((text_x, text_y), conf_text, fill="red", font=font)
    
    return image

def create_crop_with_context(image, box, padding=50):
    """Create a cropped image with contextual padding."""
    img_width, img_height = image.size
    
    crop_box = [
        max(0, box[0] - padding),
        max(0, box[1] - padding),
        min(img_width, box[2] + padding),
        min(img_height, box[3] + padding)
    ]
    
    cropped_img = image.crop(crop_box)
    
    # Adjust box coordinates relative to the crop
    relative_box = [
        box[0] - crop_box[0],
        box[1] - crop_box[1],
        box[2] - crop_box[0],
        box[3] - crop_box[1]
    ]
    
    return cropped_img, relative_box

def generate_figure(example, args, figure_index):
    """Generate an academic-quality figure of the example image with annotations."""
    try:
        # Load the original image
        original_image = Image.open(example['path'])
        img_width, img_height = original_image.size
        
        # Create a copy for drawing boxes
        annotated_image = original_image.copy()
        
        # Draw boxes on the annotated image
        annotated_image = draw_boxes_with_confidence(annotated_image, example['detections'], line_width=2)
        
        # If include_cropped is True, create cropped versions of selected boxes
        cropped_images = []
        if args.include_cropped:
            # Select a few representative boxes (e.g., highest confidence, smallest, largest)
            detections = example['detections']
            
            # Sort by confidence (descending)
            sorted_by_confidence = sorted(detections, key=lambda x: x['confidence'], reverse=True)
            
            # Get highest confidence detection
            if sorted_by_confidence:
                high_conf_box = sorted_by_confidence[0]['box']
                cropped_high_conf, rel_box = create_crop_with_context(original_image, high_conf_box)
                draw = ImageDraw.Draw(cropped_high_conf)
                
                # Draw dashed rectangle on the cropped image
                dash_length = 6
                dash_gap = 3
                x0, y0, x1, y1 = rel_box
                
                for x in range(int(x0), int(x1), dash_length + dash_gap):
                    end_x = min(x + dash_length, x1)
                    draw.line([(x, y0), (end_x, y0)], fill="red", width=2)
                    draw.line([(x, y1), (end_x, y1)], fill="red", width=2)
                
                for y in range(int(y0), int(y1), dash_length + dash_gap):
                    end_y = min(y + dash_length, y1)
                    draw.line([(x0, y), (x0, end_y)], fill="red", width=2)
                    draw.line([(x1, y), (x1, end_y)], fill="red", width=2)
                
                conf_text = f"{sorted_by_confidence[0]['confidence']:.0%}"
                draw.rectangle([(x0 + 3 - 1, y0 + 3 - 1), (x0 + 3 + 30, y0 + 3 + 15)], fill="white")
                draw.text((x0 + 3, y0 + 3), conf_text, fill="red")
                
                cropped_images.append(("Highest Confidence", cropped_high_conf))
            
            # Get a smaller detection (possibly a distant flag)
            # Calculate relative sizes
            for det in detections:
                det['relative_size'] = ((det['box'][2] - det['box'][0]) * 
                                      (det['box'][3] - det['box'][1])) / (img_width * img_height)
            
            sorted_by_size = sorted(detections, key=lambda x: x['relative_size'])
            if len(sorted_by_size) > 2:
                small_box = sorted_by_size[1]['box']  # Second smallest to avoid extremely tiny boxes
                cropped_small, rel_box = create_crop_with_context(original_image, small_box, padding=70)
                draw = ImageDraw.Draw(cropped_small)
                
                # Draw dashed rectangle on the cropped image
                dash_length = 6
                dash_gap = 3
                x0, y0, x1, y1 = rel_box
                
                for x in range(int(x0), int(x1), dash_length + dash_gap):
                    end_x = min(x + dash_length, x1)
                    draw.line([(x, y0), (end_x, y0)], fill="red", width=2)
                    draw.line([(x, y1), (end_x, y1)], fill="red", width=2)
                
                for y in range(int(y0), int(y1), dash_length + dash_gap):
                    end_y = min(y + dash_length, y1)
                    draw.line([(x0, y), (x0, end_y)], fill="red", width=2)
                    draw.line([(x1, y), (x1, end_y)], fill="red", width=2)
                
                conf_text = f"{sorted_by_size[1]['confidence']:.0%}"
                draw.rectangle([(x0 + 3 - 1, y0 + 3 - 1), (x0 + 3 + 30, y0 + 3 + 15)], fill="white")
                draw.text((x0 + 3, y0 + 3), conf_text, fill="red")
                
                cropped_images.append(("Small/Distant Detection", cropped_small))
        
        # Create figure
        if args.include_cropped and cropped_images:
            # Figure with original, annotated, and crops
            fig = plt.figure(figsize=(12, 10))
            gs = gridspec.GridSpec(2, 2, height_ratios=[3, 1])
            
            # Original image
            ax0 = plt.subplot(gs[0, 0])
            ax0.imshow(np.array(original_image))
            ax0.set_title("Original Image")
            ax0.axis('off')
            
            # Annotated image
            ax1 = plt.subplot(gs[0, 1])
            ax1.imshow(np.array(annotated_image))
            ax1.set_title(f"All Detections ({example['box_count']} boxes)")
            ax1.axis('off')
            
            # Cropped images
            for i, (title, img) in enumerate(cropped_images):
                ax = plt.subplot(gs[1, i])
                ax.imshow(np.array(img))
                ax.set_title(title)
                ax.axis('off')
            
        else:
            # Simple figure with original and annotated
            fig = plt.figure(figsize=(12, 6))
            gs = gridspec.GridSpec(1, 2)
            
            # Original image
            ax0 = plt.subplot(gs[0, 0])
            ax0.imshow(np.array(original_image))
            ax0.set_title("Original Image")
            ax0.axis('off')
            
            # Annotated image
            ax1 = plt.subplot(gs[0, 1])
            ax1.imshow(np.array(annotated_image))
            ax1.set_title(f"All Detections ({example['box_count']} boxes)")
            ax1.axis('off')
        
        # Add overall figure title
        plt.suptitle(f"Figure {figure_index}: Example of Complex Detection ({example['town']}, {example['box_count']} boxes)", 
                    fontsize=16, y=0.98)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save the figure
        output_path = os.path.join(args.output_dir, f"complex_example_{figure_index}.png")
        plt.savefig(output_path, dpi=args.dpi, bbox_inches='tight')
        plt.close()
        
        print(f"Generated figure {figure_index}: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating figure for {example['path']}: {e}")
        return None

def generate_preprocessing_figure(example, args):
    """Generate a figure showing transformation from multi-box to individual classification tasks."""
    try:
        # Load the original image
        original_image = Image.open(example['path'])
        img_width, img_height = original_image.size
        
        # Create a copy for drawing boxes
        annotated_image = original_image.copy()
        annotated_image = draw_boxes_with_confidence(annotated_image, example['detections'], line_width=2)
        
        # Select 3-4 diverse examples to show range of processing outcomes
        detections = example['detections']
        
        # Sort by confidence and size for diverse examples
        sorted_by_conf = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        # Calculate relative sizes
        for det in detections:
            det['relative_size'] = ((det['box'][2] - det['box'][0]) * 
                                  (det['box'][3] - det['box'][1])) / (img_width * img_height)
        
        sorted_by_size = sorted(detections, key=lambda x: x['relative_size'])
        
        # Get position (y-coordinate) to show position-aware processing
        for det in detections:
            det['position'] = (det['box'][1] + det['box'][3]) / (2 * img_height)  # Normalized y-center
        
        sorted_by_position = sorted(detections, key=lambda x: x['position'])
        
        # Select diverse examples: highest confidence, smallest, largest, and highest position
        selected_examples = []
        if sorted_by_conf:
            selected_examples.append(("High Confidence", sorted_by_conf[0]))
        
        if len(sorted_by_size) > 2:
            selected_examples.append(("Small/Distant Object", sorted_by_size[1]))
        
        if len(sorted_by_size) > 0:
            selected_examples.append(("Large Object", sorted_by_size[-1]))
        
        if len(sorted_by_position) > 0:
            # Find one that's not already selected
            for det in sorted_by_position:
                if det not in [x[1] for x in selected_examples] and det['position'] < 0.3:
                    selected_examples.append(("Upper Position", det))
                    break
        
        # Limit to 3-4 examples
        selected_examples = selected_examples[:4]
        
        # Create crops with context
        cropped_images = []
        for title, det in selected_examples:
            padding = max(50, int(100 * (1 - det['relative_size'])))  # More padding for smaller objects
            cropped_img, rel_box = create_crop_with_context(original_image, det['box'], padding=padding)
            
            # Draw box on crop
            draw = ImageDraw.Draw(cropped_img)
            
            # Draw dashed rectangle
            dash_length = 6
            dash_gap = 3
            x0, y0, x1, y1 = rel_box
            
            for x in range(int(x0), int(x1), dash_length + dash_gap):
                end_x = min(x + dash_length, x1)
                draw.line([(x, y0), (end_x, y0)], fill="red", width=2)
                draw.line([(x, y1), (end_x, y1)], fill="red", width=2)
            
            for y in range(int(y0), int(y1), dash_length + dash_gap):
                end_y = min(y + dash_length, y1)
                draw.line([(x0, y), (x0, end_y)], fill="red", width=2)
                draw.line([(x1, y), (x1, end_y)], fill="red", width=2)
            
            conf_text = f"{det['confidence']:.0%}"
            draw.rectangle([(x0 + 3 - 1, y0 + 3 - 1), (x0 + 3 + 30, y0 + 3 + 15)], fill="white")
            draw.text((x0 + 3, y0 + 3), conf_text, fill="red")
            
            cropped_images.append((title, cropped_img))
        
        # Create figure with original and processed versions
        fig = plt.figure(figsize=(12, 9))
        gs = gridspec.GridSpec(2, 2)
        
        # Original image
        ax0 = plt.subplot(gs[0, 0])
        ax0.imshow(np.array(original_image))
        ax0.set_title("A. Original Image")
        ax0.axis('off')
        
        # Annotated image
        ax1 = plt.subplot(gs[0, 1])
        ax1.imshow(np.array(annotated_image))
        ax1.set_title(f"B. Detected Objects ({example['box_count']} boxes)")
        ax1.axis('off')
        
        # Cropped examples - arrange in grid
        for i, (title, img) in enumerate(cropped_images):
            row = 1 + i // 2
            col = i % 2
            if row < 2:  # Only using second row
                ax = plt.subplot(gs[row, col])
                ax.imshow(np.array(img))
                ax.set_title(f"{chr(67+i)}. {title}")  # C, D, E, F...
                ax.axis('off')
        
        # Add overall figure title
        plt.suptitle("Transformation of Multi-Box Image into Classification-Ready Tasks", 
                     fontsize=16, y=0.98)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save the figure
        output_path = os.path.join(args.output_dir, "preprocessing_example.png")
        plt.savefig(output_path, dpi=args.dpi, bbox_inches='tight')
        plt.close()
        
        print(f"Generated preprocessing transformation figure: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating preprocessing figure: {e}")
        return None

def generate_geographic_variation_figure(args):
    """Generate a figure showing detection complexity variation across different towns."""
    try:
        # Select towns with varying complexity (from Table A1)
        town_complexity = [
            {"town": "Newcastle", "multi_box_pct": 61.5},  # Highest multi-box %
            {"town": "Belfast City", "multi_box_pct": 39.7},  # Large urban center, medium complexity
            {"town": "Dromore_Banbridge", "multi_box_pct": 14.5}  # Very low complexity
        ]
        
        towns_examples = []
        
        for town_info in town_complexity:
            town = town_info["town"]
            town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
            
            if not os.path.isdir(town_dir):
                print(f"Warning: {town} directory not found, skipping")
                continue
                
            bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
            
            try:
                with open(bbox_file, 'r') as f:
                    bbox_data = json.load(f)
                
                # Find a representative example with multiple boxes
                town_examples = []
                for image_name, detections in bbox_data.items():
                    box_count = len(detections)
                    if box_count >= 3:  # Look for reasonable multi-box examples
                        image_path = os.path.join(town_dir, image_name)
                        if os.path.exists(image_path):
                            town_examples.append({
                                'town': town,
                                'image_name': image_name,
                                'path': image_path,
                                'box_count': box_count,
                                'detections': detections,
                                'multi_box_pct': town_info["multi_box_pct"]
                            })
                
                # Sort by box count and get a good example (not too extreme)
                if town_examples:
                    town_examples.sort(key=lambda x: x['box_count'], reverse=True)
                    # Don't pick the most extreme case, but a representative one
                    example_idx = min(2, len(town_examples) - 1)
                    towns_examples.append(town_examples[example_idx])
            except Exception as e:
                print(f"Error accessing {town} data: {e}")
        
        if not towns_examples:
            print("No suitable geographic examples found.")
            return None
        
        # Create a comparison figure
        fig = plt.figure(figsize=(15, 10))
        rows = len(towns_examples)
        gs = gridspec.GridSpec(rows, 2)
        
        for i, example in enumerate(towns_examples):
            try:
                # Load the original image
                original_image = Image.open(example['path'])
                
                # Create a copy for drawing boxes
                annotated_image = original_image.copy()
                annotated_image = draw_boxes_with_confidence(annotated_image, example['detections'])
                
                # Original image
                ax0 = plt.subplot(gs[i, 0])
                ax0.imshow(np.array(original_image))
                ax0.set_title(f"{example['town']} (Multi-Box: {example['multi_box_pct']}%)")
                ax0.axis('off')
                
                # Annotated image
                ax1 = plt.subplot(gs[i, 1])
                ax1.imshow(np.array(annotated_image))
                ax1.set_title(f"Detected Objects: {example['box_count']} boxes")
                ax1.axis('off')
                
            except Exception as e:
                print(f"Error processing {example['town']} example: {e}")
        
        # Add overall figure title
        plt.suptitle("Geographic Variation in Detection Complexity", fontsize=16, y=0.98)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save the figure
        output_path = os.path.join(args.output_dir, "geographic_variation.png")
        plt.savefig(output_path, dpi=args.dpi, bbox_inches='tight')
        plt.close()
        
        print(f"Generated geographic variation figure: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating geographic variation figure: {e}")
        return None

def main():
    args = parse_arguments()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Find extreme examples
    print(f"Finding top {args.num_examples} images with the most bounding boxes...")
    examples = find_extreme_examples(args.num_examples)
    
    if not examples:
        print("No suitable examples found.")
        return
    
    print(f"Found {len(examples)} examples. Generating figures...")
    
    # Generate a figure for each example
    figure_paths = []
    for i, example in enumerate(examples):
        print(f"Processing example {i+1}/{len(examples)}: {example['town']}/{example['image_name']} with {example['box_count']} boxes")
        figure_path = generate_figure(example, args, i+1)
        if figure_path:
            figure_paths.append(figure_path)
    
    # Generate preprocessing transformation figure using the most extreme example
    if examples:
        print("\nGenerating preprocessing transformation figure...")
        preprocessing_path = generate_preprocessing_figure(examples[0], args)
        if preprocessing_path:
            figure_paths.append(preprocessing_path)
    
    # Generate geographic variation figure
    print("\nGenerating geographic variation figure...")
    geo_path = generate_geographic_variation_figure(args)
    if geo_path:
        figure_paths.append(geo_path)
    
    print(f"\nGenerated {len(figure_paths)} figures in {args.output_dir}")
    print("\nTo include these figures in your methodology document:")
    print("1. Copy the figures to your document's directory")
    print("2. Add figure references in the appropriate sections")

if __name__ == "__main__":
    main()