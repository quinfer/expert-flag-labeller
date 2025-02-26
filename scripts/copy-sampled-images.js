import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Copies a stratified sample of flag images to the public directory for expert labeling.
 * 
 * This script:
 * 1. Fetches the stratified sample from the API endpoint
 * 2. Creates necessary directories in public/images
 * 3. Copies only the sampled images while maintaining town-based directory structure
 * 
 * Directory Structure:
 * - Source: data/true_positive_masked_images/{town}/{image}
 * - Target: public/images/{town}/{image}
 * 
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If source images cannot be found or if copying fails
 */
async function copySampledImages() {
  try {
    const response = await fetch('http://localhost:3000/api/images');
    const { images } = await response.json();

    if (!fs.existsSync('public/images')) {
      fs.mkdirSync('public/images', { recursive: true });
    }

    let successCount = 0;
    let errorCount = 0;

    function sanitizeTownName(town) {
      return town.toUpperCase().replace(/\s+/g, '_');
    }

    for (const image of images) {
      try {
        // Original source path (keep spaces as they are in original directory)
        const sourcePath = path.join(process.cwd(), 'data', 'true_positive_masked_images', image.town, image.filename);
        
        // Log the exact source path and check if it exists
        console.log('\nProcessing image:');
        console.log('Source path:', sourcePath);
        console.log('File exists:', fs.existsSync(sourcePath));
        
        // Create sanitized target path
        const sanitizedTown = sanitizeTownName(image.town);
        const targetDir = path.join(process.cwd(), 'public/images', sanitizedTown);
        const targetPath = path.join(targetDir, image.filename);
        
        console.log('Target path:', targetPath);

        if (!fs.existsSync(sourcePath)) {
          throw new Error(`Source file not found: ${sourcePath}`);
        }

        if (!fs.existsSync(targetDir)) {
          fs.mkdirSync(targetDir, { recursive: true });
        }

        fs.copyFileSync(sourcePath, targetPath);
        successCount++;
        
        // Verify the copy
        if (fs.existsSync(targetPath)) {
          console.log('Successfully copied to:', targetPath);
        } else {
          throw new Error('File was not copied successfully');
        }

      } catch (err) {
        errorCount++;
        console.error(`\nError processing ${image.filename}:`, err.message);
      }
    }

    console.log('\nCopy Summary:');
    console.log(`Successfully copied: ${successCount} images`);
    console.log(`Failed to copy: ${errorCount} images`);

  } catch (error) {
    console.error('Failed to copy sampled images:', error);
    throw error;
  }
}

// Execute the script
copySampledImages()
  .catch(error => {
    console.error('Script failed:', error);
    process.exit(1);
  });
