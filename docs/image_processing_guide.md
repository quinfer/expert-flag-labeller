# Image Processing Guide

This comprehensive guide covers all aspects of image processing for the Expert Flag Labeler application. It documents the complete workflow from raw images to web-ready classification images.

## Overview of the Image Pipeline

The image processing pipeline manages the conversion of raw flag detection data into classification-ready images that appear in the web application. The process involves several key steps:

1. **Image Preprocessing**: Convert raw images with bounding boxes into cropped and composite images
2. **Stratified Sampling**: Select a representative subset of images for classification
3. **Web Integration**: Make images accessible to the web application
4. **Composite Image Creation**: Generate side-by-side views for proper context
5. **Verification**: Ensure all images are properly prepared and accessible

## Prerequisites

Before starting, ensure you have:

1. Python 3.6+ installed
2. Node.js 14+ installed 
3. All raw images stored in `/data/true_positive_images/{TOWN}/` directories
4. Bounding box data in `/data/true_positive_images/{TOWN}/true_positive_bboxes_hf_{TOWN}.json` files
5. Required Python packages: pillow, numpy

## Complete Workflow

### Step 1: Preprocessing Images with Contextual Cropping

The preprocessing script handles all image preparation, including cropping flags from larger scenes, adding bounding boxes, and creating composite images.

```bash
# Basic preprocessing with side-by-side views
python scripts/prepare_images_for_classification.py --side-by-side --copy-to-public

# With additional options for quality control
python scripts/prepare_images_for_classification.py \
  --side-by-side \
  --min-confidence 0.3 \
  --min-size 0.005 \
  --copy-to-public \
  --auto-clean
```

#### Key Parameters Explained

- `--side-by-side`: Creates composite views showing both the cropped flag and original context
- `--min-confidence 0.3`: Only includes detections with at least 30% confidence
- `--min-size 0.005`: Only includes objects at least 0.5% of the image area
- `--copy-to-public`: Automatically copies processed images to the public directory
- `--auto-clean`: Cleans output directories before processing

#### Full Parameter Reference

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--min-confidence` | Minimum confidence score threshold | 0.3 |
| `--min-size` | Minimum relative size as percentage of image | 0.005 |
| `--output-dir` | Output directory for cropped images | data/cropped_images_for_classification |
| `--queue-file` | Output JSON file path | data/classification_queue.json |
| `--random-sample` | Randomly sample N images from each town | All images |
| `--max-per-town` | Maximum number of images to process per town | No limit |
| `--towns` | Comma-separated list of specific towns to process | All towns |
| `--town` | Process a single specific town | None |
| `--auto-threshold` | Automatically adjust thresholds | False |
| `--highlight` | Highlight the bounding box in the cropped image | True |
| `--line-width` | Width of bounding box line | 1 |
| `--dashed` | Use dashed lines for bounding boxes | True |
| `--show-confidence` | Show confidence scores on bounding boxes | True |
| `--stats` | Show detailed statistics about the dataset | False |
| `--no-clean` | Skip cleaning the output directory | False |
| `--auto-clean` | Automatically clean the output directory | False |
| `--web-path` | Web-accessible base path for images in JSON | /images |
| `--copy-to-public` | Copy processed images to the public directory | False |
| `--public-dir` | Public directory for web-accessible images | public/images |
| `--side-by-side` | Create side-by-side views | False |

#### What This Step Produces

- Cropped images in `/data/cropped_images_for_classification/`
- Composite side-by-side images (if `--side-by-side` used)
- A classification queue JSON file at `/data/classification_queue.json`
- Copies of images in `/public/images/{TOWN}/` (if `--copy-to-public` used)

### Step 2: Generate Image List for the Web Application

This step creates a JavaScript and JSON file that the application uses to locate and display images.

```bash
node scripts/generate-image-list.js
```

This script:
- Scans the `/public/images` directory recursively
- Creates a list of all image paths with town information
- Saves this as `src/data/images.json` and `src/data/images.js`

### Step 3: Prepare Static Images for Reliable Serving

To ensure reliable image loading in development and production, we copy a subset of images to the static directory.

```bash
node scripts/copy-images-to-static.js
```

This script:
- Selects and copies images to `/public/static/{TOWN}/` directories
- Generates `src/data/static-images.js` and `src/data/static-images.json`
- Ensures composite images are properly handled

### Step 4: Verify Composite Images

If you're experiencing issues with composite images, run the verification script:

```bash
node scripts/verify-composite-images.js
```

This script:
- Scans all classification queues to check for missing composite images
- Reports missing composites by town
- Provides guidance for fixing any issues

## Implementing Stratified Sampling

For more research-aligned sampling, we implement a stratified approach that ensures proportional representation across towns, accounting for:

1. Geographical distribution (all towns)
2. Detection complexity (multi-box percentages)
3. Total image counts per town
4. Flag size and visibility conditions

### The Stratified Sampling Process

```bash
# Step 1: Create and run the analysis script
python scripts/analyze_towns.py

# Step 2: Run the generated commands
chmod +x stratified_commands.sh
./stratified_commands.sh
```

This approach:
- Analyzes town distributions and multi-box percentages
- Calculates optimal sample sizes for each town
- Generates town-specific preprocessing commands
- Creates separate queue files that are later merged

The sampling algorithm:
1. Allocates a base sample size proportional to town size
2. Applies additional weighting based on multi-box percentage
3. Ensures minimum representation from small towns
4. Caps sample size for very large towns to prevent domination
5. Rebalances to achieve the target sample size

## Understanding Multi-Box Images

One of the key challenges in this dataset is handling images with multiple bounding boxes:

- **37.4% of images** contain multiple flag detections
- Some images have up to **36 bounding boxes**
- Towns vary significantly in multi-box percentages (14.3% to 61.5%)

The preprocessing handles multi-box images by:
1. Creating individual crops for each bounding box
2. Adding contextual padding proportional to object size  
3. Highlighting the specific detection with dashed lines
4. Creating side-by-side composites showing both the crop and original context

File naming follows these patterns:
- Cropped: `{imagename}_box{index}.jpg`
- Composite: `composite_{imagename}_box{index}.jpg`

## Troubleshooting

### Missing Composite Images

If composite images are not displaying in the app:

1. Verify that you've run the preprocessing with the `--side-by-side` flag
2. Check that composite images exist in the data directory:
   ```bash
   find data/cropped_images_for_classification -name "composite_*" | head
   ```
3. Regenerate composites if needed:
   ```bash
   python scripts/prepare_images_for_classification.py --side-by-side --copy-to-public
   ```
4. Re-run the copy script to update the static directory:
   ```bash
   node scripts/copy-images-to-static.js
   ```
5. Use the verification tool:
   ```bash
   node scripts/verify-composite-images.js
   ```
6. Regenerate missing composites:
   ```bash
   python scripts/generate_missing_composites.py
   ```

### Memory and Disk Space Issues

Processing large datasets may require significant resources:

- Increase the `--min-confidence` threshold (e.g., 0.4 or 0.5)
- Decrease the `--random-sample` count
- Process towns in batches using the `--town` parameter
- Ensure at least 10GB of free disk space for the full pipeline

### Image Access Testing

To verify image loading:

1. Check the static test pages:
   - Visit `/static-test.html` - Direct HTML test
   - Visit `/static-test-full` - React component test
   - Visit `/test-path` - Path format test

2. Verify image counts:
   ```bash
   # Count classification queue entries
   python -c "import json; f=open('data/classification_queue.json'); data=json.load(f); print(f\"Total images: {data['metadata']['total_images']}\")"
   
   # Count static images
   find public/static -type f | wc -l
   
   # Count composite images
   find public/static -name "composite_*" | wc -l
   ```

## Best Practices

For optimal results:

1. **Always use `--side-by-side`**: Ensures experts see both the cropped flag and original context
2. **Use stratified sampling**: Balances town representation and detection complexity
3. **Verify images after preprocessing**: Run the verification script to check for issues
4. **Keep preprocessing parameters consistent**: Use the same thresholds across batches
5. **Run the full pipeline in order**: Preprocessing → Generate Image List → Copy to Static

## Understanding the Output Files

The preprocessing creates several key outputs:

1. **Cropped Images**: Individual images focused on each bounding box
2. **Composite Images**: Side-by-side views showing context (prefixed with `composite_`)
3. **Classification Queue JSON**: Contains metadata about all processed images
4. **Web-Optimized Images**: Copies in public and static directories for the web app

These files work together to provide a seamless classification experience in the web application.