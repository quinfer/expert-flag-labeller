import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get current directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Path to your images directories
const imagesDir = path.join(projectRoot, 'public', 'images');
const staticDir = path.join(projectRoot, 'public', 'static');

// Function to get all images recursively
function getAllImages(dir) {
  let results = [];
  
  try {
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const itemPath = path.join(dir, item);
      const stat = fs.statSync(itemPath);
      
      if (stat.isDirectory()) {
        // If it's a directory (town folder), get images inside
        const nestedImages = getAllImages(itemPath);
        results = results.concat(nestedImages);
      } else if (stat.isFile() && /\.(jpg|jpeg|png|gif)$/i.test(item)) {
        // If it's an image file
        const town = path.basename(dir); // Get the town name from directory
        const relativePath = itemPath.replace(path.join(projectRoot, 'public'), '');
        
        // Handle paths for development and production
        // In development, we want to make sure the path starts with a slash
        // for direct access from the public directory
        const publicPath = relativePath.replace(/\\/g, '/'); // Ensure forward slashes for web paths
        
        // Create basic image info
        const imageInfo = {
          town,
          path: publicPath.startsWith('/') ? publicPath : `/${publicPath}`, // Ensure it starts with a slash
          filename: item
        };
        
        // Check if this is a boxed image (has _box{number}.jpg in filename but not _boxed.jpg)
        // Skip adding composite info for files that are already composite files
        if (!item.startsWith('composite_')) {
          const isBoxed = item.includes('_boxed');
          const isBoxed2 = /_box\d+\.jpg$/.test(item); // Matches _box0.jpg, _box1.jpg etc.
          const needsComposite = !isBoxed && isBoxed2;
          
          if (needsComposite) {
            // Create the composite filename and path
            const compositeFilename = `composite_${item}`;
            const compositePath = `/static/${town.toUpperCase()}/${compositeFilename}`;
            
            // Add composite information
            imageInfo.composite_image = compositePath;
            imageInfo.has_composite = true;
            
            // Debug info
            console.log(`Added composite info for ${item}: ${compositePath}`);
          }
        }
        
        results.push(imageInfo);
      }
    }
  } catch (err) {
    console.error(`Error processing directory ${dir}:`, err.message);
  }
  
  return results;
}

try {
  // Get images from both directories
  const imagesFromImagesDir = getAllImages(imagesDir);
  const imagesFromStaticDir = getAllImages(staticDir);
  
  // Create a map to eliminate duplicates, with static directory images taking precedence
  const imageMap = new Map();
  
  // Add images from /images directory first
  imagesFromImagesDir.forEach(img => {
    imageMap.set(img.filename, img);
  });
  
  // Then add/override with images from /static directory
  imagesFromStaticDir.forEach(img => {
    imageMap.set(img.filename, img);
  });
  
  // Convert back to array
  const allImages = Array.from(imageMap.values());
  
  // Create directory if it doesn't exist
  const dataDir = path.join(projectRoot, 'src', 'data');
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  // Write to a JSON file only
  fs.writeFileSync(
    path.join(projectRoot, 'src', 'data', 'images.json'),
    JSON.stringify(allImages, null, 2)
  );
  
  console.log(`Generated list of ${allImages.length} images`);
} catch (error) {
  console.error('Error generating image list:', error);
}
