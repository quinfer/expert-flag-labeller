import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get current directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Path to your images directory
const imagesDir = path.join(projectRoot, 'public', 'images');

// Function to get all images recursively
function getAllImages(dir) {
  let results = [];
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
      
      results.push({
        town,
        path: relativePath.replace(/\\/g, '/'), // Ensure forward slashes for web paths
        filename: item
      });
    }
  }
  
  return results;
}

try {
  const allImages = getAllImages(imagesDir);
  
  // Create directory if it doesn't exist
  const dataDir = path.join(projectRoot, 'src', 'data');
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  // Write to a JSON file
  fs.writeFileSync(
    path.join(projectRoot, 'src', 'data', 'images.json'),
    JSON.stringify(allImages, null, 2)
  );
  
  // Also output as JavaScript code for direct inclusion
  const jsOutput = `// Auto-generated image list
export const staticImages = ${JSON.stringify(allImages, null, 2)};
`;
  
  fs.writeFileSync(
    path.join(projectRoot, 'src', 'data', 'images.js'),
    jsOutput
  );
  
  console.log(`Generated list of ${allImages.length} images`);
} catch (error) {
  console.error('Error generating image list:', error);
}
