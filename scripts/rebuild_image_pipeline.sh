#!/bin/bash

# Comprehensive script to rebuild the image pipeline from scratch
# This fixes the composite image path issues and ensures proper 3,000 image count

echo "=== EXPERT FLAG LABELER IMAGE PIPELINE REBUILD ==="
echo "Starting complete rebuild of image processing pipeline..."

# Change to project root directory
cd "$(dirname "$0")" || exit

# 1. Clean all directories
echo "Step 1: Cleaning all directories..."
rm -rf data/cropped_images_for_classification/*
rm -rf data/classification_queue_*.json
rm -rf public/static/*
rm -rf public/images/*
rm -f src/data/static-images.js
rm -f data/classification_queue.json

# 2. Update SimpleCompositeImage.tsx to handle path variations better
echo "Step 2: Fixing image component path handling..."
cat <<'EOF' > /tmp/SimpleCompositeImage.tsx.fix
  // Function to generate paths with the composite_ prefix
  const getCompositePaths = () => {
    // Get town in consistent format - handle space or underscore versions
    const townSegment = town.replace(/ /g, '_').toUpperCase();
    
    // Extract filename from path
    const pathParts = croppedSrc.split('/');
    const filename = pathParts[pathParts.length - 1];
    
    // Check if we already have a specific compositeSrc provided
    if (compositeSrc) {
      console.log(`Using provided composite path: ${compositeSrc}`);
      // Always prioritize the provided composite path and have fallbacks
      return [
        compositeSrc,
        `/static/${townSegment}/composite_${filename}`,
        `/images/${townSegment}/composite_${filename}`,
        croppedSrc
      ];
    }
    
    // Detect if this is a cropped image that needs a composite
    // These can be either multi-box cropped images (_box0.jpg, _box1.jpg) 
    // OR images that already have a box drawn (_boxed.jpg)
    const isBoxed = filename.includes('_boxed');
    const isBoxCropped = /_box\d+\.jpg$/.test(filename); // Matches _box0.jpg, _box1.jpg etc.
    
    // BOTH multi-box crops AND boxed images should show composite views for context
    const needsComposite = isBoxCropped || isBoxed;
    
    if (needsComposite) {
      // Create the composite filename - ensure only one underscore before the filename
      const filenameWithoutPrefix = filename.startsWith('_') ? filename.substring(1) : filename;
      const compositeFilename = `composite_${filenameWithoutPrefix}`;
      const doublePrefixCompositeFilename = `composite__${filenameWithoutPrefix}`; // Handle case with double underscores
      
      console.log(`Image is from multi-box, looking for composite: ${compositeFilename}`);
      
      // ALWAYS prioritize the /static/ path with composite_ prefix for multi-box images
      const staticPath = `/static/${townSegment}/${compositeFilename}`;
      const imagePath = `/images/${townSegment}/${compositeFilename}`;
      
      // Add fallbacks for potential path variations
      const alternativeImagePath = `/images/${townSegment}/${doublePrefixCompositeFilename}`;
      
      console.log(`Generated composite paths to try:`, [staticPath, imagePath, alternativeImagePath]);
      
      // Return paths in order of priority - static first, then images, then alternative format, then original
      return [
        staticPath,
        imagePath, 
        alternativeImagePath,
        croppedSrc
      ];
    } else {
      // For regular images (not from multi-box detections)
      console.log(`Regular image (not from multi-box): ${filename}`);
      
      // If filename already has composite prefix, use it directly
      if (filename.startsWith('composite_')) {
        return [croppedSrc];
      }
      
      // Try the regular image and a possible composite version as fallback
      // For boxed images, see if a composite version exists anyway
      const compositeFilename = `composite_${filename}`;
      const staticCompositePath = `/static/${townSegment}/${compositeFilename}`;
      const imageCompositePath = `/images/${townSegment}/${compositeFilename}`;
      
      return [
        croppedSrc,
        staticCompositePath,
        imageCompositePath
      ];
    }
  };
EOF

sed -i.bak "$(grep -n 'getCompositePaths.*=.*(.*).*{' /Users/quinference/expert-flag-labeler/src/components/SimpleCompositeImage.tsx | cut -d: -f1),$(grep -n '};$' /Users/quinference/expert-flag-labeler/src/components/SimpleCompositeImage.tsx | head -1 | cut -d: -f1) c\\
$(cat /tmp/SimpleCompositeImage.tsx.fix)" /Users/quinference/expert-flag-labeler/src/components/SimpleCompositeImage.tsx

# 3. Process each town with consistent settings
echo "Step 3: Processing images town by town..."

# Set higher confidence threshold to improve quality
MIN_CONFIDENCE=0.3

# Start with larger towns (proportional representation)
# These towns have more flags and should have more samples
for town in "BELFAST CITY" "METROPOLITAN NEWTOWNABBEY" "CARRICKFERGUS" "LISBURN CITY" "CRAIGAVON" "ANTRIM" "BALLYMENA" "LARNE" "COLERAINE" "BALLYCLARE"; do
  echo "Processing large town: $town"
  python scripts/prepare_images_for_classification.py \
    --side-by-side \
    --min-confidence $MIN_CONFIDENCE \
    --town "$town" \
    --random-sample 200 \
    --copy-to-public \
    --auto-clean \
    --queue-file "data/classification_queue_${town// /_}.json"
done

# Medium sized towns
for town in "BANGOR" "METROPOLITAN CASTLEREAGH" "METROPOLITAN LISBURN" "DERRY CITY" "BALLYMONEY" "ENNISKILLEN" "OMAGH TOWN" "DUNGANNON"; do
  echo "Processing medium town: $town"
  python scripts/prepare_images_for_classification.py \
    --side-by-side \
    --min-confidence $MIN_CONFIDENCE \
    --town "$town" \
    --random-sample 100 \
    --copy-to-public \
    --auto-clean \
    --queue-file "data/classification_queue_${town// /_}.json"
done

# Smaller towns (for diversity)
for town in "ARMAGH" "COOKSTOWN" "NEWTOWNARDS" "NEWRY" "PORTRUSH" "PORTSTEWART" "MAGHERAFELT" "LIMAVADY" "COMBER" "GREENISLAND" "KILKEEL"; do
  echo "Processing small town: $town"
  python scripts/prepare_images_for_classification.py \
    --side-by-side \
    --min-confidence $MIN_CONFIDENCE \
    --town "$town" \
    --random-sample 50 \
    --copy-to-public \
    --auto-clean \
    --queue-file "data/classification_queue_${town// /_}.json"
done

# 4. Merge all queue files
echo "Step 4: Merging queue files..."
python - <<'END_PYTHON'
import json
import glob
import os
from datetime import datetime

# Find all queue files
queue_files = glob.glob('data/classification_queue_*.json')
print(f'Found {len(queue_files)} queue files to merge')

# Merge all queues
merged_queue = {'metadata': {}, 'images': []}
total_images = 0
total_boxes = 0

for qf in queue_files:
    with open(qf, 'r') as f:
        data = json.load(f)
    merged_queue['images'].extend(data['images'])
    total_images += data['metadata'].get('total_images', 0)
    total_boxes += data['metadata'].get('total_boxes', 0)

# Update metadata
merged_queue['metadata'] = {
    'created': datetime.now().isoformat(),
    'min_confidence': 0.3,
    'min_size': 0.005,
    'total_images': total_images,
    'total_boxes': total_boxes,
    'stratified_sampling': True
}

# Write merged queue
with open('data/classification_queue.json', 'w') as f:
    json.dump(merged_queue, f, indent=2)

print(f'Merged queue created with {len(merged_queue["images"])} images')
print(f'Total images: {total_images}, Total boxes: {total_boxes}')
END_PYTHON

# 5. Copy images to static directory
echo "Step 5: Copying images to static directory..."
cat <<'EOF' > /tmp/town_paths_fix.js
// Add this snippet to fix inconsistent town naming in paths
const processSourceDir = (dir) => {
  try {
    // Get all town directories and normalize them
    const towns = fs.readdirSync(dir)
      .filter(item => fs.statSync(path.join(dir, item)).isDirectory())
      .map(town => {
        // Normalize town name: replace spaces with underscores and uppercase
        return {
          original: town,
          normalized: town.replace(/ /g, '_').toUpperCase()
        };
      });
    
    console.log(`Found ${towns.length} towns in ${dir}`);
    
    // Create a map for quick lookups
    const townMap = new Map();
    towns.forEach(({ original, normalized }) => {
      townMap.set(normalized, original);
    });
    
    return townMap;
  } catch (err) {
    console.error(`Error processing directory ${dir}:`, err);
    return new Map();
  }
};

// Process the source directory to get a mapping of normalized town names to original ones
const townMap = processSourceDir(sourceDir);
console.log(`Town mapping created for ${townMap.size} towns`);
EOF

# Insert the town_paths_fix.js code after the sourceDir declaration
sed -i.bak "/const sourceDir = path.join(projectRoot, 'public', 'images');/r /tmp/town_paths_fix.js" /Users/quinference/expert-flag-labeler/scripts/copy-images-to-static.js

# Update MAX_PER_TOWN in copy-images-to-static.js to increase representation
sed -i.bak 's/const MAX_PER_TOWN = 30;  \/\/ Reduced maximum images per town/const MAX_PER_TOWN = 100;  \/\/ Increased maximum images per town/' /Users/quinference/expert-flag-labeler/scripts/copy-images-to-static.js

# Run the copy-images-to-static.js script
node scripts/copy-images-to-static.js

# 6. Generate the image lists 
echo "Step 6: Generating image lists..."
node scripts/generate-image-list.js
node scripts/generate-composite-image-list.js

# 7. Verify path formats in images.js
echo "Step 7: Verifying path formats..."
python - <<'END_PYTHON'
import json
import os
import re

# Check the static-images.js file and report on path patterns
static_images_js = 'src/data/static-images.js'
if os.path.exists(static_images_js):
    with open(static_images_js, 'r') as f:
        content = f.read()
        # Extract just the JSON part
        json_part = re.search(r'export const staticImages = (\[.*?\]);', content, re.DOTALL)
        if json_part:
            try:
                # Add a dummy variable assignment to make it valid JSON
                json_eval = "var data = " + json_part.group(1) + ";"
                # Count various path patterns
                static_paths = len(re.findall(r'"/static/', content))
                image_paths = len(re.findall(r'"/images/', content))
                composite_paths = len(re.findall(r'"composite_image":', content))
                
                print(f"Static-images.js analysis:")
                print(f"  - Total /static/ paths: {static_paths}")
                print(f"  - Total /images/ paths: {image_paths}")
                print(f"  - Total composite_image entries: {composite_paths}")
            except Exception as e:
                print(f"Error parsing static-images.js: {e}")
else:
    print("static-images.js file not found")
END_PYTHON

# 8. Ensure API correctly limits to 3,000 images
echo "Step 8: Adding 3,000 image limit to API..."
cat <<'EOF' > /tmp/api_limit_fix.ts
    // Limit the number of images to MAX_IMAGES (set to 3000)
    const MAX_IMAGES = 3000;
    
    // If we have more than MAX_IMAGES, take a random subset
    let finalImages = imagesFromQueue;
    if (imagesFromQueue.length > MAX_IMAGES) {
      console.log(`[API] Limiting images from ${imagesFromQueue.length} to ${MAX_IMAGES}`);
      
      // Get a random sample while ensuring distribution across towns
      const imagesByTown = {};
      
      // Group by town
      imagesFromQueue.forEach(img => {
        const town = img.town || 'UNKNOWN';
        if (!imagesByTown[town]) {
          imagesByTown[town] = [];
        }
        imagesByTown[town].push(img);
      });
      
      // Calculate how many images to take from each town proportionally
      const towns = Object.keys(imagesByTown);
      const perTownCount = Math.floor(MAX_IMAGES / towns.length);
      let remainder = MAX_IMAGES - (perTownCount * towns.length);
      
      finalImages = [];
      towns.forEach(town => {
        // Calculate how many to take from this town, give extra to towns with more images
        const townImages = imagesByTown[town];
        let townAllocCount = perTownCount;
        
        // Distribute remainder to towns with more images first
        if (remainder > 0 && townImages.length > townAllocCount) {
          townAllocCount++;
          remainder--;
        }
        
        // Limit to actual number available
        townAllocCount = Math.min(townAllocCount, townImages.length);
        
        // Shuffle and take the allocated number
        const shuffled = [...townImages].sort(() => 0.5 - Math.random());
        finalImages.push(...shuffled.slice(0, townAllocCount));
      });
      
      console.log(`[API] After limiting: ${finalImages.length} images in the final set`);
    }
EOF

api_limit_line=$(grep -n "images: imagesFromQueue || \[\]," /Users/quinference/expert-flag-labeler/src/app/api/images-static/route.ts | cut -d: -f1)
if [ -n "$api_limit_line" ]; then
  sed -i.bak "${api_limit_line}s/images: imagesFromQueue || \[\],/images: finalImages || \[\],/" /Users/quinference/expert-flag-labeler/src/app/api/images-static/route.ts
  # Insert the limit code before the return statement
  api_return_line=$((api_limit_line - 2))
  sed -i.bak "${api_return_line}r /tmp/api_limit_fix.ts" /Users/quinference/expert-flag-labeler/src/app/api/images-static/route.ts
fi

# 9. Check results
echo "Step 9: Checking results..."
echo "Images in queue:"
python -c "import json; f=open('data/classification_queue.json'); data=json.load(f); print(f\"Total images: {len(data['images'])}\")"
echo "Images in static directory:"
find public/static -type f | wc -l
echo "Composite images:"
find public/static -name "composite_*" | wc -l

echo "=== REBUILD COMPLETE ==="
echo "You should now restart the server with: npm run dev"