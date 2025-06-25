#!/usr/bin/env python3
import os
import json
import glob
from collections import defaultdict

# 1. Analyze town distributions
towns_data = {}
total_images = 0
total_multibox = 0

# Load town data
base_dir = 'data/true_positive_images'
towns = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
print(f"Found {len(towns)} towns to analyze")

for town in sorted(towns):
    json_file = os.path.join(base_dir, town, f'true_positive_bboxes_hf_{town}.json')
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        # Count images and multi-box images
        town_images = len(data)
        town_multibox = sum(1 for img, boxes in data.items() if len(boxes) > 1)
        multibox_pct = town_multibox / town_images if town_images > 0 else 0
        
        towns_data[town] = {
            'total': town_images,
            'multibox': town_multibox,
            'multibox_pct': multibox_pct
        }
        
        total_images += town_images
        total_multibox += town_multibox
        
        print(f"{town}: {town_images} images, {town_multibox} multi-box ({multibox_pct*100:.1f}%)")

# Print totals
print(f"\nTotals: {total_images} images, {total_multibox} multi-box ({total_multibox/total_images*100:.1f}%)")

# 2. Calculate stratified sample sizes
target_total = 3000  # Reduced target for classification to limit to ~3000 images
min_per_town = 10    # Reduced minimum images from each town
total_alloc = 0

# Allocate samples based on town size and multibox percentage
for town, stats in towns_data.items():
    # Base allocation proportional to town size
    base_alloc = int(target_total * (stats['total'] / total_images))
    
    # Adjust by multibox percentage (towns with more multibox images get more samples)
    multibox_factor = 1.5 if stats['multibox_pct'] > 0.4 else \
                      1.3 if stats['multibox_pct'] > 0.3 else \
                      1.0
    
    town_alloc = max(min_per_town, int(base_alloc * multibox_factor))
    
    # Cap at reasonable maximum to prevent oversampling huge towns
    town_alloc = min(town_alloc, 400)
    
    towns_data[town]['sample_size'] = town_alloc
    total_alloc += town_alloc

# Scale to match target total
print(f"\nInitial allocation: {total_alloc} images (target: {target_total})")
if total_alloc != target_total:
    scale_factor = target_total / total_alloc
    final_alloc = 0
    
    for town in towns_data:
        original = towns_data[town]['sample_size']
        towns_data[town]['sample_size'] = max(min_per_town, 
                                         int(towns_data[town]['sample_size'] * scale_factor))
        final_alloc += towns_data[town]['sample_size']
    
    print(f"After scaling: {final_alloc} images")

# 3. Generate bash commands
print("\n# Commands to run for stratified sampling:")
with open('stratified_commands.sh', 'w') as f:
    f.write("#!/bin/bash\n\n")
    f.write("# Auto-generated stratified sampling commands\n\n")
    
    # First clean all output directories
    f.write("# Clean output directories\n")
    f.write("rm -rf data/cropped_images_for_classification/*\n")
    f.write("rm -rf data/classification_queue_*.json\n\n")
    
    for town, stats in sorted(towns_data.items(), key=lambda x: x[1]['multibox_pct'], reverse=True):
        sample_size = stats['sample_size']
        town_cmd = f"# Processing {town}: {sample_size} images ({stats['multibox_pct']*100:.1f}% multi-box)\n"
        town_cmd += f"python scripts/prepare_images_for_classification.py \\\n"
        town_cmd += f"  --side-by-side \\\n"
        town_cmd += f"  --min-confidence 0.3 \\\n"
        town_cmd += f"  --town \"{town}\" \\\n"
        town_cmd += f"  --random-sample {sample_size} \\\n"
        town_cmd += f"  --copy-to-public \\\n"
        town_cmd += f"  --queue-file \"data/classification_queue_{town}.json\"\n\n"
        
        f.write(town_cmd)
        print(town_cmd)
    
    # Add a command to merge the queue files
    f.write("# Merge all queue files\n")
    f.write("python - <<'END_PYTHON'\n")
    f.write("import json\n")
    f.write("import glob\n")
    f.write("import os\n\n")
    f.write("# Find all queue files\n")
    f.write("queue_files = glob.glob('data/classification_queue_*.json')\n")
    f.write("print(f'Found {len(queue_files)} queue files to merge')\n\n")
    f.write("# Merge all queues\n")
    f.write("merged_queue = {'metadata': {}, 'images': []}\n")
    f.write("total_images = 0\n")
    f.write("total_boxes = 0\n\n")
    f.write("for qf in queue_files:\n")
    f.write("    with open(qf, 'r') as f:\n")
    f.write("        data = json.load(f)\n")
    f.write("    merged_queue['images'].extend(data['images'])\n")
    f.write("    total_images += data['metadata'].get('total_images', 0)\n")
    f.write("    total_boxes += data['metadata'].get('total_boxes', 0)\n\n")
    f.write("# Update metadata\n")
    f.write("merged_queue['metadata'] = {\n")
    f.write("    'created': data['metadata'].get('created', ''),\n")
    f.write("    'min_confidence': 0.3,\n")
    f.write("    'min_size': 0.005,\n")
    f.write("    'total_images': total_images,\n")
    f.write("    'total_boxes': total_boxes,\n")
    f.write("    'stratified_sampling': True\n")
    f.write("}\n\n")
    f.write("# Write merged queue\n")
    f.write("with open('data/classification_queue.json', 'w') as f:\n")
    f.write("    json.dump(merged_queue, f, indent=2)\n\n")
    f.write("print(f'Merged queue created with {len(merged_queue[\"images\"])} images')\n")
    f.write("print(f'Total images: {total_images}, Total boxes: {total_boxes}')\n")
    f.write("END_PYTHON\n\n")
    
    # Add a command to run the copy-to-static.js script
    f.write("# Run the copy-to-static script\n")
    f.write("node scripts/copy-images-to-static.js\n\n")
    
    # Add a command to generate the composite image list
    f.write("# Generate the composite image list\n")
    f.write("node scripts/generate-composite-image-list.js\n\n")
    
    # Add a command to check results
    f.write("# Check results\n")
    f.write("echo 'Images in queue:'\n")
    f.write("python -c \"import json; f=open('data/classification_queue.json'); data=json.load(f); print(f\\\"Total images: {len(data['images'])}\\\")\"\n")
    f.write("echo 'Images in static directory:'\n")
    f.write("find public/static -type f | wc -l\n")
    f.write("echo 'Composite images:'\n")
    f.write("find public/static -name \"composite_*\" | wc -l\n\n")

print("\nCommands have been saved to stratified_commands.sh")
print("Run 'chmod +x stratified_commands.sh' and then './stratified_commands.sh' to execute")