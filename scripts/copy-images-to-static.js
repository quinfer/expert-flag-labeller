import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import ProgressBar from 'progress';

// Get current directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Helper function to shuffle an array (Fisher-Yates algorithm)
function shuffleArray(array) {
  const newArray = [...array];
  for (let i = newArray.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
  }
  return newArray;
}

// Source and destination paths
const sourceDir = path.join(projectRoot, 'public', 'images');
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
const destDir = path.join(projectRoot, 'public', 'static');

// Create destination directory if it doesn't exist
if (!fs.existsSync(destDir)) {
  fs.mkdirSync(destDir, { recursive: true });
  console.log(`Created destination directory: ${destDir}`);
}

// Function to clean the destination directory before copying
function cleanDestinationDirectory() {
  try {
    // Check if destination directory exists 
    if (fs.existsSync(destDir)) {
      console.log("Cleaning static directory to ensure only composite images remain...");
      
      // For each town subdirectory
      const towns = fs.readdirSync(destDir).filter(item => 
        fs.statSync(path.join(destDir, item)).isDirectory()
      );
      
      let totalRemoved = 0;
      
      for (const town of towns) {
        const townDir = path.join(destDir, town);
        const files = fs.readdirSync(townDir);
        
        // Remove any non-composite files
        for (const file of files) {
          if (!file.startsWith('composite_') && !file.includes('_boxed')) {
            fs.unlinkSync(path.join(townDir, file));
            totalRemoved++;
          }
        }
      }
      
      console.log(`Removed ${totalRemoved} non-composite images from static directory`);
    }
  } catch (error) {
    console.error("Error cleaning destination directory:", error);
  }
}

// Clean destination directory before copying
cleanDestinationDirectory();

// Function to copy a sample of images from each town
function copySampleImages() {
  try {
    // Get list of town directories
    const towns = fs.readdirSync(sourceDir);
    console.log(`Found ${towns.length} towns in ${sourceDir}`);
    
    // Create a progress bar for town processing
    const townBar = new ProgressBar('Processing towns [:bar] :current/:total :percent :etas', {
      complete: '=',
      incomplete: ' ',
      width: 30,
      total: towns.length
    });
    
    // Define max images per town and total max images
    const MAX_PER_TOWN = 100;  // Increased maximum images per town
    const MAX_TOTAL_IMAGES = 3000;  // Maximum total images (for Vercel limits)
    
    // Track statistics
    let totalCopied = 0;
    
    // Calculate base images per town to distribute evenly
    const baseImagesPerTown = Math.min(
      MAX_PER_TOWN,
      Math.floor(MAX_TOTAL_IMAGES / towns.length)
    );
    
    console.log(`Using baseline of ${baseImagesPerTown} images per town (max ${MAX_PER_TOWN})`);
    
    // Process each town
    for (const town of towns) {
      // Update progress bar
      townBar.tick({town: town});
      
      const townSourceDir = path.join(sourceDir, town);
      const townDestDir = path.join(destDir, town);
      
      // Skip if not a directory
      if (!fs.statSync(townSourceDir).isDirectory()) {
        continue;
      }
      
      // Create town destination directory
      if (!fs.existsSync(townDestDir)) {
        fs.mkdirSync(townDestDir, { recursive: true });
      }
      
      // Get all images in the town directory
      const images = fs.readdirSync(townSourceDir).filter(file => 
        file.endsWith('.jpg') || file.endsWith('.jpeg') || file.endsWith('.png')
      );
      
      // Group images by their base name (without the composite_ prefix)
      // This ensures we keep pairs of regular and composite images together
      const imageGroups = {};
      
      // Process all images and organize them into groups by base name
      images.forEach(img => {
        // Extract the base name, removing 'composite_' prefix if present
        let baseName;
        if (img.startsWith('composite_')) {
          baseName = img.substring('composite_'.length);
        } else {
          baseName = img;
        }
        
        // Create group if it doesn't exist
        if (!imageGroups[baseName]) {
          imageGroups[baseName] = {
            regular: null,
            composite: null
          };
        }
        
        // Add to the appropriate slot
        if (img.startsWith('composite_')) {
          imageGroups[baseName].composite = img;
        } else {
          imageGroups[baseName].regular = img;
        }
      });
      
      // Convert to array of groups for easier processing
      const groupsArray = Object.entries(imageGroups).map(([baseName, group]) => ({
        baseName,
        ...group
      }));
      
      // Shuffle the groups for random selection
      const shuffledGroups = shuffleArray(groupsArray);
      
      // Select up to baseImagesPerTown groups
      const selectedGroups = shuffledGroups.slice(0, baseImagesPerTown);
      
      // Flatten into image list, keeping both regular and corresponding composite images
      // This maintains the stratified random sample while ensuring composite images are available
      let imagesToCopy = [];
      selectedGroups.forEach(group => {
        // For cropped images - BOTH multi-box crops AND images with boxes drawn
        // These have either "_box{number}" OR "_boxed" in their filename
        const isCroppedImage = group.regular && 
                              (/_box\d+\.jpg$/.test(group.regular) || 
                               group.regular.includes('_boxed'));
                                 
        if (isCroppedImage) {
          // If we have a composite, always use that
          if (group.composite) {
            imagesToCopy.push(group.composite);
            // Add original too for reference
            imagesToCopy.push(group.regular);
          } 
          // If no composite but we have the boxed image, try harder to find it
          else {
            console.log(`Warning: Missing composite for cropped image ${group.regular} - searching harder`);
            
            // Add the regular image regardless
            imagesToCopy.push(group.regular);
            
            // Attempt to create a composite filename and check if it exists elsewhere in the source dir
            const possibleCompositeFilename = `composite_${group.regular}`;
            const possibleCompositePath = path.join(townSourceDir, possibleCompositeFilename);
            
            if (fs.existsSync(possibleCompositePath)) {
              console.log(`Found matching composite at ${possibleCompositePath}`);
              imagesToCopy.push(possibleCompositeFilename);
            } else {
              // Try to find the composite in the data/cropped_images_for_classification directory
              const croppedDir = path.join(projectRoot, 'data', 'cropped_images_for_classification', town);
              if (fs.existsSync(croppedDir)) {
                const altCompositePath = path.join(croppedDir, possibleCompositeFilename);
                if (fs.existsSync(altCompositePath)) {
                  console.log(`Found composite in cropped_images directory: ${altCompositePath}`);
                  // Copy to the source dir first
                  fs.copyFileSync(altCompositePath, possibleCompositePath);
                  // Then add to images to copy
                  imagesToCopy.push(possibleCompositeFilename);
                } else {
                  console.warn(`Could not find composite for ${group.regular} anywhere - app will fall back to cropped image`);
                }
              } else {
                console.warn(`Could not find composite for ${group.regular} - app will fall back to cropped image`);
              }
            }
          }
        }
        // For regular flagged images or boxed images (single flag case)
        else {
          // Add both regular and composite if they exist
          if (group.regular) {
            imagesToCopy.push(group.regular);
          }
          if (group.composite) {
            imagesToCopy.push(group.composite);
          }
        }
      });
      
      console.log(`Copying ${imagesToCopy.length} images from ${town}...`);
      
      // Check if we're approaching the total limit
      if (totalCopied + imagesToCopy.length > MAX_TOTAL_IMAGES) {
        // Truncate to stay under the limit
        imagesToCopy = imagesToCopy.slice(0, MAX_TOTAL_IMAGES - totalCopied);
        console.log(`  Truncated to ${imagesToCopy.length} to stay under total limit`);
      }
      
      // Create a progress bar for copying images in this town
      const imageBar = new ProgressBar(`  ${town} [:bar] :current/:total :percent :etas`, {
        complete: '=',
        incomplete: ' ',
        width: 20,
        total: imagesToCopy.length
      });
      
      // Copy each sampled image
      for (const image of imagesToCopy) {
        const sourcePath = path.join(townSourceDir, image);
        const destPath = path.join(townDestDir, image);
        
        fs.copyFileSync(sourcePath, destPath);
        totalCopied++;
        imageBar.tick();
        
        // Stop if we've reached the total limit
        if (totalCopied >= MAX_TOTAL_IMAGES) {
          console.log(`Reached maximum total of ${MAX_TOTAL_IMAGES} images, stopping copy process`);
          break;
        }
      }
      
      // Stop town processing if we've reached the total limit
      if (totalCopied >= MAX_TOTAL_IMAGES) {
        break;
      }
    }
    
    console.log(`\nSuccessfully copied ${totalCopied} images to ${destDir}`);
    console.log(`Images should now be accessible at /static/{TOWN}/{filename}`);
    
    // Generate a direct access HTML file for testing
    generateTestHtml();
    
    return totalCopied;
  } catch (error) {
    console.error('Error copying images:', error);
    return 0;
  }
}

// Function to generate a test HTML file
function generateTestHtml() {
  const testHtmlPath = path.join(projectRoot, 'public', 'static-test.html');
  const towns = fs.readdirSync(destDir).filter(item => 
    fs.statSync(path.join(destDir, item)).isDirectory()
  );
  
  // Generate HTML content with samples from each town
  let htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <title>Static Images Test</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    h1, h2 { margin-bottom: 16px; }
    .town { margin-bottom: 30px; border: 1px solid #ddd; padding: 16px; }
    .images { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
    .image-card { border: 1px solid #eee; padding: 8px; }
    img { max-width: 100%; height: auto; }
    .path { font-family: monospace; font-size: 12px; margin-top: 8px; word-break: break-all; }
  </style>
</head>
<body>
  <h1>Static Images Test</h1>
  <p>This page tests if images can be loaded from the /static directory.</p>
`;

  // Add sections for each town
  for (const town of towns) {
    const townDir = path.join(destDir, town);
    const images = fs.readdirSync(townDir).filter(file => 
      file.endsWith('.jpg') || file.endsWith('.jpeg') || file.endsWith('.png')
    );
    
    if (images.length === 0) continue;
    
    htmlContent += `
  <div class="town">
    <h2>${town}</h2>
    <div class="images">
`;
    
    // Add images for this town (just show first 5 for the test page)
    for (const image of images.slice(0, 5)) {
      const imagePath = `/static/${town}/${image}`;
      
      htmlContent += `
      <div class="image-card">
        <img src="${imagePath}" alt="${image}" />
        <div class="path">${imagePath}</div>
      </div>
`;
    }
    
    htmlContent += `
    </div>
  </div>
`;
  }
  
  htmlContent += `
</body>
</html>
`;
  
  // Write the HTML file
  fs.writeFileSync(testHtmlPath, htmlContent);
  console.log(`Generated test HTML file at: ${testHtmlPath}`);
  console.log(`Test page should be accessible at: http://localhost:3000/static-test.html`);
}

// Execute the main function
const copiedCount = copySampleImages();

// Update images.js to include the new static paths
if (copiedCount > 0) {
  console.log('\nUpdating images.js to include static paths...');
  
  // Get the static image paths
  const staticImages = [];
  const towns = fs.readdirSync(destDir).filter(item => 
    fs.statSync(path.join(destDir, item)).isDirectory()
  );
  
  for (const town of towns) {
    const townDir = path.join(destDir, town);
    const images = fs.readdirSync(townDir).filter(file => 
      file.endsWith('.jpg') || file.endsWith('.jpeg') || file.endsWith('.png')
    );
    
    for (const image of images) {
      staticImages.push({
        town,
        path: `/static/${town}/${image}`,
        filename: image
      });
    }
  }
  
  // Write to a new JS file
  const jsContent = `// Auto-generated static image list
export const staticImages = ${JSON.stringify(staticImages, null, 2)};
`;
  
  fs.writeFileSync(
    path.join(projectRoot, 'src', 'data', 'static-images.js'),
    jsContent
  );
  
  console.log(`Generated static-images.js with ${staticImages.length} images`);
}