# Image Loading in the Expert Flag Labeler

This document explains how the image loading system works in this application.

## Image Processing Workflow

1. **Image Generation**: Images are initially created and stored in `data/cropped_images_for_classification` using the `sample_cropped_for_public.py` script.

2. **Image Copying**: To make images accessible in the web application, we use a two-step process:
   - First, run `python scripts/sample_cropped_for_public.py` which copies images to the `public/images/{TOWN}` directory
   - Then, run `node scripts/generate-image-list.js` to create a list of image paths in `src/data/images.js`

3. **Static Images**: For more reliable serving in development mode, a sample of images is also copied to the `public/static` directory:
   - Run `node scripts/copy-images-to-static.js` to copy images to `public/static/{TOWN}` and generate `src/data/static-images.js`
   - The application will prioritize these static images if available

## Troubleshooting Image Loading

If images are not displaying in the application:

1. Verify that you've run the scripts in this order:
   ```
   python scripts/sample_cropped_for_public.py
   node scripts/generate-image-list.js
   node scripts/copy-images-to-static.js
   ```

2. Check that images exist in both directories:
   - `public/images/{TOWN}/`
   - `public/static/{TOWN}/`

3. Verify that the image files are properly referenced in:
   - `src/data/images.js`
   - `src/data/static-images.js`

4. Test static image loading with:
   - Visit `/static-test.html` - A direct HTML file testing image loading
   - Visit `/static-test-full` - A React page testing static image loading

## Understanding the Solution

The application uses a multi-layered approach to ensure images load correctly:

1. First tries to load images from the API route `/api/images-static`
2. Falls back to static images from `src/data/static-images.js`
3. Finally falls back to the original images from `src/data/images.js`

Image paths are structured as `/static/{TOWN}/{FILENAME}` or `/images/{TOWN}/{FILENAME}` to maintain consistent access regardless of the deployment environment.

## Image Placeholder

If an image fails to load, a placeholder is automatically displayed. The placeholder is served from the `/placeholder` route.

## Testing Image Access

For debugging image loading issues, visit:
- `/static-test.html`: Tests direct HTML image loading
- `/static-test-full`: Tests React component image loading
- `/test-path`: Tests various image path formats