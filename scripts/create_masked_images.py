import os
import json
import argparse
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
from collections import Counter
import subprocess
import platform
import time
import webbrowser
import sys

# Base directories
BASE_DIR = "data"
TRUE_POSITIVE_DIR = os.path.join(BASE_DIR, "true_positive_images")
OUTPUT_DIR = os.path.join(BASE_DIR, "true_positive_masked_images")

# Bounding box expansion settings
BOX_EXPANSION = 20  # Number of pixels to expand the box in each direction

# Manual overrides for specific images (if needed)
MANUAL_OVERRIDES = {}

# Function to draw dashed rectangle
def draw_dashed_rectangle(draw, box, color, width=1, dash_length=5, space_length=5):
    """Draw a dashed rectangle on the image."""
    x0, y0, x1, y1 = box
    
    # Convert all coordinates to integers for drawing
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    
    # Draw top line
    for x in range(x0, x1, dash_length + space_length):
        end = min(x + dash_length, x1)
        draw.line([(x, y0), (end, y0)], fill=color, width=width)
    
    # Draw right line
    for y in range(y0, y1, dash_length + space_length):
        end = min(y + dash_length, y1)
        draw.line([(x1, y), (x1, end)], fill=color, width=width)
    
    # Draw bottom line
    for x in range(x1, x0, -dash_length - space_length):
        end = max(x - dash_length, x0)
        draw.line([(x, y1), (end, y1)], fill=color, width=width)
    
    # Draw left line
    for y in range(y1, y0, -dash_length - space_length):
        end = max(y - dash_length, y0)
        draw.line([(x0, y), (x0, end)], fill=color, width=width)

def create_masked_image(image_path, detections, output_path):
    """Create a masked image with bounding boxes and confidence scores."""
    try:
        # Check if there's a manual override for this image
        town_name = os.path.basename(os.path.dirname(image_path))
        image_name = os.path.basename(image_path)
        
        if town_name in MANUAL_OVERRIDES and image_name in MANUAL_OVERRIDES[town_name]:
            print(f"Using manual override for {town_name}/{image_name}")
            detections = MANUAL_OVERRIDES[town_name][image_name]
        
        # Open and convert image
        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        
        # Draw each detection
        for detection in detections:
            # Get bounding box coordinates and confidence
            original_box = detection['box']
            confidence = detection['confidence']
            
            # Make a copy of the box to avoid modifying the original data
            box = original_box.copy()
            
            # Ensure all coordinates are float for consistent expansion
            box = [float(coord) for coord in box]
            
            # Print original box coordinates for debugging (console only)
            print(f"Original box: {box}")
            
            # Expand the box by BOX_EXPANSION pixels in each direction
            expanded_box = [
                box[0] - BOX_EXPANSION,  # x1 (left edge moves left)
                box[1] - BOX_EXPANSION,  # y1 (top edge moves up)
                box[2] + BOX_EXPANSION,  # x2 (right edge moves right)
                box[3] + BOX_EXPANSION   # y2 (bottom edge moves down)
            ]
            
            # Draw dashed rectangle with expanded box
            draw_dashed_rectangle(draw, expanded_box, "red", width=2)
            
            # Draw confidence score
            text_y_pos = expanded_box[1] - 15
            draw.text((expanded_box[0], text_y_pos), f"Conf: {confidence:.2f}", fill="blue")
        
        # Save the masked image
        image.save(output_path)
        return True
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return False

def process_town_images(town):
    """Process images for a single town."""
    print(f"\nProcessing town: {town}")
    
    # Load bounding box metadata - updated path
    town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
    bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
    try:
        with open(bbox_file, 'r') as f:
            bbox_data = json.load(f)
        print(f"Loaded bounding box data for {town}")
    except Exception as e:
        print(f"Error loading bounding box data for {town}: {e}")
        return
    
    # Create output directory for this town
    town_output_dir = os.path.join(OUTPUT_DIR, town)
    os.makedirs(town_output_dir, exist_ok=True)
    
    # Get list of images in the town directory
    images = [f for f in os.listdir(town_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    print(f"Found {len(images)} images in {town}")
    
    # Process each image
    for image_name in tqdm(images, desc=f"Processing {town}"):
        input_path = os.path.join(town_dir, image_name)
        output_path = os.path.join(town_output_dir, f"masked_{image_name}")
        
        if image_name in bbox_data:
            detections = bbox_data[image_name]
            success = create_masked_image(input_path, detections, output_path)
            if success:
                print(f"Created masked image: {output_path}")
        else:
            print(f"No bounding box data found for {image_name}")

def analyze_bounding_boxes():
    """Analyze the JSON files to count images with multiple bounding boxes."""
    print("\nAnalyzing bounding box data across all towns...")
    
    # Get list of towns
    towns = [d for d in os.listdir(TRUE_POSITIVE_DIR) 
             if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, d))]
    
    total_images = 0
    images_with_boxes = 0
    images_with_multiple_boxes = 0
    box_count_distribution = Counter()
    
    # Process each town
    for town in tqdm(towns, desc="Analyzing towns"):
        town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
        bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
        
        try:
            with open(bbox_file, 'r') as f:
                bbox_data = json.load(f)
            
            # Count images in this town
            town_images = [f for f in os.listdir(town_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
            total_images += len(town_images)
            
            # Count images with bounding boxes
            images_with_boxes_in_town = len(bbox_data)
            images_with_boxes += images_with_boxes_in_town
            
            # Count images with multiple bounding boxes
            for image_name, detections in bbox_data.items():
                box_count = len(detections)
                box_count_distribution[box_count] += 1
                
                if box_count > 1:
                    images_with_multiple_boxes += 1
                    print(f"Image with {box_count} boxes: {town}/{image_name}")
            
        except Exception as e:
            print(f"Error analyzing {town}: {e}")
    
    # Print summary
    print("\nBounding Box Analysis Summary:")
    print(f"Total images: {total_images}")
    print(f"Images with bounding boxes: {images_with_boxes} ({images_with_boxes/total_images*100:.1f}%)")
    print(f"Images with multiple bounding boxes: {images_with_multiple_boxes} ({images_with_multiple_boxes/images_with_boxes*100:.1f}% of images with boxes)")
    
    print("\nDistribution of bounding box counts:")
    for count in sorted(box_count_distribution.keys()):
        num_images = box_count_distribution[count]
        print(f"  {count} box(es): {num_images} images ({num_images/images_with_boxes*100:.1f}%)")
    
    return box_count_distribution

def open_file(file_path):
    """Open a file with the default application."""
    try:
        print(f"Attempting to open: {file_path}")
        print("(The image should open in your default image viewer, not in the terminal)")
        
        # Try using webbrowser module first (more reliable across platforms)
        if os.path.exists(file_path):
            file_url = f"file://{os.path.abspath(file_path)}"
            print(f"Opening URL: {file_url}")
            if webbrowser.open(file_url):
                return True
        
        # Fall back to platform-specific methods if webbrowser fails
        if platform.system() == 'Darwin':  # macOS
            print("Using macOS 'open' command...")
            result = subprocess.run(['open', file_path], check=False)
            return result.returncode == 0
        elif platform.system() == 'Windows':  # Windows
            print("Using Windows shell command...")
            result = subprocess.run(['start', '', file_path], shell=True, check=False)
            return result.returncode == 0
        else:  # Linux
            print("Using Linux 'xdg-open' command...")
            result = subprocess.run(['xdg-open', file_path], check=False)
            return result.returncode == 0
    except Exception as e:
        print(f"Error opening file: {e}")
        print(f"You can manually open the file at: {os.path.abspath(file_path)}")
        return False

def find_images_with_multiple_boxes(min_boxes=2):
    """Find all images with multiple bounding boxes and return them as a list.
    
    Args:
        min_boxes: Minimum number of boxes required (default: 2)
    """
    print(f"\nFinding images with at least {min_boxes} bounding boxes...")
    
    # Get list of towns
    towns = [d for d in os.listdir(TRUE_POSITIVE_DIR) 
             if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, d))]
    
    multi_box_images = []
    
    # Process each town
    for town in tqdm(towns, desc="Scanning towns"):
        town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
        bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
        
        try:
            with open(bbox_file, 'r') as f:
                bbox_data = json.load(f)
            
            # Find images with multiple bounding boxes
            for image_name, detections in bbox_data.items():
                if len(detections) >= min_boxes:
                    image_path = os.path.join(town_dir, image_name)
                    if os.path.exists(image_path):
                        multi_box_images.append({
                            'town': town,
                            'image_name': image_name,
                            'path': image_path,
                            'box_count': len(detections)
                        })
            
        except Exception as e:
            print(f"Error scanning {town}: {e}")
    
    # Sort by box count (descending)
    multi_box_images.sort(key=lambda x: x['box_count'], reverse=True)
    
    print(f"Found {len(multi_box_images)} images with at least {min_boxes} bounding boxes")
    return multi_box_images

def save_image_paths_to_file(images, output_file="image_paths.txt"):
    """Save a list of image paths to a file for manual viewing."""
    with open(output_file, 'w') as f:
        f.write("# Image Paths for Manual Viewing\n")
        f.write("# Copy and paste these paths into your file explorer\n\n")
        
        for i, img in enumerate(images):
            f.write(f"# Image {i+1}: {img['town']}/{img['image_name']} ({img['box_count']} boxes)\n")
            f.write(f"Original: {os.path.abspath(img['path'])}\n")
            
            # Calculate masked image path
            town_output_dir = os.path.join(OUTPUT_DIR, img['town'])
            masked_path = os.path.join(town_output_dir, f"masked_{img['image_name']}")
            
            if os.path.exists(masked_path):
                f.write(f"Masked: {os.path.abspath(masked_path)}\n")
            else:
                f.write(f"Masked: (not yet created)\n")
            
            f.write("\n")
    
    print(f"\nImage paths saved to: {os.path.abspath(output_file)}")
    print("You can open this file and copy-paste paths to your file explorer")
    return os.path.abspath(output_file)

def manual_viewer(min_boxes=2, vscode_mode=False):
    """Interactive viewer for images with multiple bounding boxes.
    
    Args:
        min_boxes: Minimum number of boxes required (default: 2)
        vscode_mode: If True, save paths to file instead of trying to open directly
    """
    # Find all images with multiple boxes
    multi_box_images = find_images_with_multiple_boxes(min_boxes)
    
    if not multi_box_images:
        print(f"No images with at least {min_boxes} bounding boxes found.")
        return
    
    # Create a directory for the viewer output
    viewer_dir = os.path.join(OUTPUT_DIR, "multi_box_viewer")
    os.makedirs(viewer_dir, exist_ok=True)
    
    # In VS Code mode, just save paths and exit
    if vscode_mode:
        paths_file = os.path.join(viewer_dir, "image_paths.txt")
        save_image_paths_to_file(multi_box_images, paths_file)
        
        # Process all images to create masked versions
        print("\nCreating masked versions of all images...")
        for image_info in tqdm(multi_box_images, desc="Processing images"):
            town = image_info['town']
            image_name = image_info['image_name']
            image_path = image_info['path']
            
            # Create masked version
            town_output_dir = os.path.join(OUTPUT_DIR, town)
            os.makedirs(town_output_dir, exist_ok=True)
            masked_path = os.path.join(town_output_dir, f"masked_{image_name}")
            
            if not os.path.exists(masked_path):
                # Load bounding box data
                bbox_file = os.path.join(TRUE_POSITIVE_DIR, town, f"true_positive_bboxes_hf_{town}.json")
                try:
                    with open(bbox_file, 'r') as f:
                        bbox_data = json.load(f)
                    
                    # Create masked image
                    detections = bbox_data[image_name]
                    create_masked_image(image_path, detections, masked_path)
                except Exception as e:
                    print(f"Error creating masked image for {town}/{image_name}: {e}")
        
        print(f"\nAll done! Open the file at {paths_file} to see the image paths.")
        return
    
    # Process and display images
    current_index = 0
    total_images = len(multi_box_images)
    
    print("\nManual Viewer for Images with Multiple Bounding Boxes")
    print("-----------------------------------------------------")
    print("NOTE: Images will open in your default image viewer application (not in the terminal)")
    print("Commands:")
    print("  n: Next image")
    print("  p: Previous image")
    print("  v: View original image")
    print("  m: View masked image with bounding boxes")
    print("  i: Show image info")
    print("  f: Change minimum box filter")
    print("  o: Show file location (to open manually)")
    print("  q: Quit viewer")
    
    while True:
        # Get current image info
        image_info = multi_box_images[current_index]
        town = image_info['town']
        image_name = image_info['image_name']
        image_path = image_info['path']
        box_count = image_info['box_count']
        
        # Create masked version if it doesn't exist
        town_output_dir = os.path.join(OUTPUT_DIR, town)
        os.makedirs(town_output_dir, exist_ok=True)
        masked_path = os.path.join(town_output_dir, f"masked_{image_name}")
        
        if not os.path.exists(masked_path):
            # Load bounding box data
            bbox_file = os.path.join(TRUE_POSITIVE_DIR, town, f"true_positive_bboxes_hf_{town}.json")
            try:
                with open(bbox_file, 'r') as f:
                    bbox_data = json.load(f)
                
                # Create masked image
                detections = bbox_data[image_name]
                create_masked_image(image_path, detections, masked_path)
                print(f"Created masked image: {masked_path}")
            except Exception as e:
                print(f"Error creating masked image: {e}")
                continue
        
        # Display image info
        print(f"\n[{current_index + 1}/{total_images}] {town}/{image_name}")
        print(f"Bounding boxes: {box_count}")
        
        # Get user command
        cmd = input("Command (n/p/v/m/i/f/o/q): ").lower()
        
        if cmd == 'q':
            print("Exiting viewer.")
            break
        elif cmd == 'n':
            current_index = (current_index + 1) % total_images
        elif cmd == 'p':
            current_index = (current_index - 1) % total_images
        elif cmd == 'v':
            print(f"Opening original image: {image_path}")
            success = open_file(image_path)
            if not success:
                print(f"Failed to open image automatically.")
                print(f"Try opening it manually at: {os.path.abspath(image_path)}")
        elif cmd == 'm':
            print(f"Opening masked image: {masked_path}")
            success = open_file(masked_path)
            if not success:
                print(f"Failed to open image automatically.")
                print(f"Try opening it manually at: {os.path.abspath(masked_path)}")
        elif cmd == 'i':
            # Load bounding box data to show detailed info
            bbox_file = os.path.join(TRUE_POSITIVE_DIR, town, f"true_positive_bboxes_hf_{town}.json")
            try:
                with open(bbox_file, 'r') as f:
                    bbox_data = json.load(f)
                
                detections = bbox_data[image_name]
                print("\nDetailed bounding box information:")
                for i, detection in enumerate(detections):
                    box = detection['box']
                    confidence = detection['confidence']
                    print(f"  Box {i+1}: {box}, Confidence: {confidence:.2f}")
            except Exception as e:
                print(f"Error loading detailed info: {e}")
        elif cmd == 'f':
            try:
                new_min = int(input("Enter new minimum number of boxes: "))
                if new_min < 1:
                    print("Minimum boxes must be at least 1")
                else:
                    # Restart viewer with new filter
                    print(f"Restarting viewer with minimum {new_min} boxes...")
                    return manual_viewer(new_min, vscode_mode=vscode_mode)
            except ValueError:
                print("Please enter a valid number")
        elif cmd == 'o':
            print(f"\nOriginal image location: {os.path.abspath(image_path)}")
            print(f"Masked image location: {os.path.abspath(masked_path)}")
            print("You can open these files directly in Finder/Explorer")
        else:
            print("Invalid command. Use n (next), p (previous), v (view), m (masked), i (info), f (filter), o (location), q (quit)")
    
    return

def main():
    """Main execution function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Create masked images with bounding boxes.')
    parser.add_argument('--test', action='store_true', help='Run in test mode on a single town')
    parser.add_argument('--town', type=str, help='Specific town to process (for test mode)')
    parser.add_argument('--limit', type=int, default=5, help='Number of images to process in test mode')
    parser.add_argument('--image', type=str, help='Process a specific image (requires --town)')
    parser.add_argument('--analyze', action='store_true', help='Analyze bounding box data without creating images')
    parser.add_argument('--viewer', action='store_true', help='Launch interactive viewer for images with multiple boxes')
    parser.add_argument('--min-boxes', type=int, default=2, help='Minimum number of boxes for viewer (default: 2)')
    parser.add_argument('--vscode', action='store_true', help='VS Code terminal mode: save paths to file instead of opening directly')
    args = parser.parse_args()
    
    # Create base output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Created output directory: {OUTPUT_DIR}")
    
    # Detect if running in VS Code terminal
    in_vscode = args.vscode or "VSCODE_PID" in os.environ
    if in_vscode:
        print("Detected VS Code environment. Using file-based viewing mode.")
    
    # Launch manual viewer if requested
    if args.viewer:
        manual_viewer(args.min_boxes, vscode_mode=in_vscode)
        return
    
    # Analyze bounding box data if requested
    if args.analyze:
        analyze_bounding_boxes()
        return
    
    # Process a specific image if requested
    if args.image and args.town:
        town = args.town
        image_name = args.image
        
        town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
        input_path = os.path.join(town_dir, image_name)
        
        if not os.path.exists(input_path):
            print(f"Image not found: {input_path}")
            return
            
        town_output_dir = os.path.join(OUTPUT_DIR, town)
        os.makedirs(town_output_dir, exist_ok=True)
        output_path = os.path.join(town_output_dir, f"masked_{image_name}")
        
        # Check if we have a manual override
        if town in MANUAL_OVERRIDES and image_name in MANUAL_OVERRIDES[town]:
            detections = MANUAL_OVERRIDES[town][image_name]
            print(f"Using manual override for {town}/{image_name}")
        else:
            # Try to load from JSON
            bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
            try:
                with open(bbox_file, 'r') as f:
                    bbox_data = json.load(f)
                if image_name in bbox_data:
                    detections = bbox_data[image_name]
                else:
                    print(f"No bounding box data found for {image_name}")
                    return
            except Exception as e:
                print(f"Error loading bounding box data: {e}")
                return
        
        success = create_masked_image(input_path, detections, output_path)
        if success:
            print(f"Created masked image: {output_path}")
        return
    
    # Test mode - process a single town with limited images
    if args.test:
        if args.town:
            test_town = args.town
            if not os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, test_town)):
                print(f"Town '{test_town}' not found. Available towns:")
                for town in os.listdir(TRUE_POSITIVE_DIR):
                    if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, town)):
                        print(f"  - {town}")
                return
        else:
            # Find the first available town
            available_towns = [d for d in os.listdir(TRUE_POSITIVE_DIR) 
                              if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, d))]
            if not available_towns:
                print("No towns found in the data directory.")
                return
            test_town = available_towns[0]
            print(f"No town specified. Using first available town: {test_town}")
        
        # Process the test town with limited images
        print(f"TEST MODE: Processing town '{test_town}' with limit of {args.limit} images")
        
        # Modify process_town_images for test mode
        test_process_town(test_town, limit=args.limit)
        
        print(f"Test completed. Check the output directory: {os.path.join(OUTPUT_DIR, test_town)}")
    else:
        # Normal mode - process all towns
        towns = [d for d in os.listdir(TRUE_POSITIVE_DIR) 
                if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, d))]
        
        print(f"Found {len(towns)} towns to process")
        
        # Process each town
        for town in tqdm(towns, desc="Processing towns"):
            process_town_images(town)

def test_process_town(town, limit=5):
    """Process a limited number of images from a town for testing."""
    print(f"\nTEST: Processing town: {town}")
    
    # Load bounding box metadata - updated path
    town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
    bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
    try:
        with open(bbox_file, 'r') as f:
            bbox_data = json.load(f)
        print(f"Loaded bounding box data for {town}")
        
        # Print a sample of the data structure
        sample_image = next(iter(bbox_data))
        print(f"\nSample data structure for image '{sample_image}':")
        print(json.dumps(bbox_data[sample_image][:1], indent=2))
    except Exception as e:
        print(f"Error loading bounding box data for {town}: {e}")
        return
    
    # Create output directory for this town
    town_output_dir = os.path.join(OUTPUT_DIR, town)
    os.makedirs(town_output_dir, exist_ok=True)
    
    # Get list of images in the town directory
    all_images = [f for f in os.listdir(town_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    # Filter to only images that have bounding box data
    images_with_data = [img for img in all_images if img in bbox_data]
    
    if not images_with_data:
        print(f"No images with bounding box data found for {town}")
        return
    
    # Limit the number of images to process
    test_images = images_with_data[:min(limit, len(images_with_data))]
    
    print(f"TEST: Found {len(all_images)} total images, {len(images_with_data)} with bounding box data")
    print(f"TEST: Processing {len(test_images)} images")
    
    # Process each test image
    for image_name in tqdm(test_images, desc=f"Processing test images for {town}"):
        input_path = os.path.join(town_dir, image_name)
        output_path = os.path.join(town_output_dir, f"masked_{image_name}")
        
        detections = bbox_data[image_name]
        success = create_masked_image(input_path, detections, output_path)
        if success:
            print(f"Created masked image: {output_path}")

if __name__ == "__main__":
    main()