import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get current directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Source and destination paths
const sourceDir = path.join(projectRoot, 'public', 'images');
const destDir = path.join(projectRoot, 'public', 'static');

// Create destination directory if it doesn't exist
if (!fs.existsSync(destDir)) {
  fs.mkdirSync(destDir, { recursive: true });
  console.log(`Created destination directory: ${destDir}`);
}

// Function to copy a sample of images from each town
function copySampleImages() {
  try {
    // Get list of town directories
    const towns = fs.readdirSync(sourceDir);
    console.log(`Found ${towns.length} towns in ${sourceDir}`);
    
    // Track statistics
    let totalCopied = 0;
    
    // Process each town
    for (const town of towns) {
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
      
      // Sample up to 10 images from each town
      const samplesToTake = Math.min(10, images.length);
      const sampledImages = images.slice(0, samplesToTake);
      
      console.log(`Copying ${sampledImages.length} images from ${town}...`);
      
      // Copy each sampled image
      for (const image of sampledImages) {
        const sourcePath = path.join(townSourceDir, image);
        const destPath = path.join(townDestDir, image);
        
        fs.copyFileSync(sourcePath, destPath);
        totalCopied++;
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
    
    // Add images for this town
    for (const image of images.slice(0, 5)) { // Just show first 5 images
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