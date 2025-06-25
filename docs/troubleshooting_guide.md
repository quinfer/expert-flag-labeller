# Troubleshooting Guide

This guide provides comprehensive solutions for common issues with the Expert Flag Labeler application. Whether you're experiencing problems with image loading, composite views, or deployment, you'll find step-by-step resolution instructions here.

## Image Loading Issues

### Problem: Images Not Displaying in the Application

If images are not appearing on the classification page:

#### Step 1: Verify Image Processing Steps

Ensure you've run all required scripts in the correct order:

```bash
# Step 1: Process images with side-by-side view
python scripts/prepare_images_for_classification.py --side-by-side --copy-to-public

# Step 2: Generate image list
node scripts/generate-image-list.js

# Step 3: Copy to static directory
node scripts/copy-images-to-static.js
```

#### Step 2: Check Image Directories

Verify that images exist in both required directories:

```bash
# Check public images
ls -la public/images/{TOWN}/

# Check static images
ls -la public/static/{TOWN}/
```

#### Step 3: Verify Image Files References

Check that image files are properly referenced in the required files:

```bash
# Check image.js exists and has content
cat src/data/images.js | head

# Check static-images.js exists and has content
cat src/data/static-images.js | head
```

#### Step 4: Test Static Image Loading

Use the built-in test pages to check image loading:

- Visit `/static-test.html` - A direct HTML file testing image loading
- Visit `/static-test-full` - A React page testing static image loading
- Visit `/test-path` - A test for different path formats

#### Step 5: Restart Development Server

Sometimes a restart is needed to pick up new images:

```bash
# Stop the current server (Ctrl+C) then restart
npm run dev
```

## Composite Image Issues

### Problem: Missing Side-by-Side Composite Views

If the app shows only single cropped images without the side-by-side context view:

#### Step 1: Check if Composite Images Exist

```bash
# Look for composite images in the data directory
find data/cropped_images_for_classification -name "composite_*" | head

# Check if composite images were copied to public directory
find public/images -name "composite_*" | head

# Check if composite images are in the static directory
find public/static -name "composite_*" | head
```

#### Step 2: Run Diagnostic Verification

```bash
# Run the composite verification script
node scripts/verify-composite-images.js
```

This will scan all classification queue files and check if corresponding composite images exist, providing a report of missing composites by town.

#### Step 3: Regenerate Side-by-Side Images

If composites are missing, regenerate them with:

```bash
# For all images
python scripts/prepare_images_for_classification.py --side-by-side --copy-to-public

# For specific towns with missing composites
python scripts/prepare_images_for_classification.py --side-by-side --town TOWN_NAME --copy-to-public
```

Replace `TOWN_NAME` with the town you need to process (e.g., `ANTRIM`).

#### Step 4: Update Static Images

After regenerating composites, update the static directory:

```bash
# Copy updated composite images to static directory
node scripts/copy-images-to-static.js
```

#### Step 5: Generate Missing Composites Only

For targeted fixing of just the missing composites:

```bash
# Generate only missing composite images
python scripts/generate_missing_composites.py
```

This script identifies and regenerates only missing composites without reprocessing all images.

## Classification Queue Issues

### Problem: No Images in Classification Queue

If the application shows no images to classify:

#### Step 1: Check Queue File Exists

```bash
# Check if the classification queue file exists
ls -la data/classification_queue.json

# Check the content of the queue file
cat data/classification_queue.json | head
```

#### Step 2: Check Queue File Content

```bash
# Check the number of images in the queue
python -c "import json; f=open('data/classification_queue.json'); data=json.load(f); print(f\"Total images: {data['metadata']['total_images']}\nTotal boxes: {data['metadata']['total_boxes']}\")"
```

#### Step 3: Regenerate Queue File

If the queue is empty or corrupted, regenerate it:

```bash
# Process a small sample to create a new queue
python scripts/prepare_images_for_classification.py --random-sample 50 --auto-clean
```

## Deployment Issues

### Problem: Images Not Showing in Production

If images work locally but not in the deployed version:

#### Step 1: Verify Build Process

Ensure your build process includes image files:

```bash
# Build the application
npm run build
```

Check the console for any warnings about large static assets.

#### Step 2: Check Production Image Paths

Verify that the image paths use the correct format. Production may require adjustments to image paths. Check the app's image components (`SimpleCompositeImage.tsx` and others) to ensure they handle production paths correctly.

#### Step 3: Optimize Image Count for Production

If you're approaching size limits for your deployment platform:

```bash
# Create a smaller sample for production
python scripts/prepare_images_for_classification.py --random-sample 100 --side-by-side --copy-to-public --auto-clean
```

Then regenerate image lists and static files as usual.

## Authentication Issues

### Problem: Unable to Log In

If you're experiencing login issues:

#### Step 1: Check Credentials

Verify that you're using the correct username format (first name only) and password.

#### Step 2: Clear Browser Cache and Cookies

Sometimes authentication tokens can become corrupt:

1. Open browser settings
2. Clear cookies and site data for the application URL
3. Refresh and try logging in again

#### Step 3: Check Authentication API

If login is still not working:

1. Open browser dev tools (F12)
2. Go to the Network tab
3. Try logging in and observe the network requests for auth errors

## Development Environment Issues

### Problem: Dependencies or Build Errors

If you're having trouble with dependencies or build errors:

#### Step 1: Update Dependencies

```bash
# Update npm packages
npm install

# Clear npm cache if needed
npm cache clean --force
```

#### Step 2: Check Node.js Version

Ensure you're using a compatible Node.js version (18+):

```bash
# Check node version
node -v

# Update if needed (using nvm or similar)
nvm install 18
nvm use 18
```

## Performance Issues

### Problem: Slow Image Loading or Classification

If the application is performing slowly:

#### Step 1: Optimize Image Counts

Reduce the number of images in the static directory:

```bash
# Create a more optimized set for development
node scripts/copy-images-to-static.js --limit 1000
```

#### Step 2: Check Browser Console

Look for repeated errors or failed requests in the browser console that might indicate underlying issues.

## Component Fixes for Composite Images

If you're still experiencing issues with composite images, the following components have been updated to better handle them:

1. **src/components/SimpleCompositeImage.tsx**:
   - Check this component for better path resolution for composite images
   - Verify it has improved fallback mechanism
   - Ensure it has enhanced debugging

2. **src/app/api/images-static/route.ts**:
   - Confirm it properly identifies multi-box images
   - Verify it adds composite paths even if not explicitly in the classification queue
   - Check that it provides logging about composite path status

## Setting Up a New Environment

If you're setting up the application in a completely new environment:

1. **Clone the repository**
2. **Install dependencies**: `npm install`
3. **Create environment variables**: `.env.local` with Supabase credentials
4. **Prepare a small test set**:
   ```bash
   python scripts/prepare_images_for_classification.py --town TOWN_NAME --random-sample 25 --side-by-side --copy-to-public
   node scripts/generate-image-list.js
   node scripts/copy-images-to-static.js
   ```
5. **Start development server**: `npm run dev`

## Getting Additional Help

If you're still experiencing issues after trying these solutions:

1. Check the browser console for specific error messages
2. Review the Node.js server logs for backend errors
3. Contact the development team with:
   - Description of the issue
   - Steps to reproduce
   - Browser and OS information
   - Screenshot of any error messages