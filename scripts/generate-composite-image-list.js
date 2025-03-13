import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get current directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Path to your classification queue JSON file
const queueFile = path.join(projectRoot, 'data', 'classification_queue.json');

// Function to generate image list with composite images
function generateCompositeImageList() {
  try {
    console.log(`Reading classification queue from ${queueFile}`);
    
    // Check if the file exists
    if (!fs.existsSync(queueFile)) {
      console.error('Classification queue file not found!');
      return;
    }
    
    // Read and parse the queue file
    const queueData = JSON.parse(fs.readFileSync(queueFile, 'utf8'));
    
    if (!queueData || !queueData.images || !Array.isArray(queueData.images)) {
      console.error('Invalid or empty classification queue file!');
      return;
    }
    
    console.log(`Found ${queueData.images.length} images in classification queue`);
    
    // Extract image information
    const imageList = queueData.images.map(item => {
      const basicInfo = {
        town: item.town,
        path: item.cropped_image || item.original_image,
        filename: item.filename
      };
      
      // Add composite image information if available
      if (item.composite_image) {
        return {
          ...basicInfo,
          composite_image: item.composite_image,
          has_composite: true
        };
      }
      
      return basicInfo;
    });
    
    // Create directory if it doesn't exist
    const dataDir = path.join(projectRoot, 'src', 'data');
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    
    // Write to a JSON file
    fs.writeFileSync(
      path.join(dataDir, 'static-images.json'),
      JSON.stringify(imageList, null, 2)
    );
    
    // Also output as JavaScript code for direct inclusion
    const jsOutput = `// Auto-generated image list with composite images
export const staticImages = ${JSON.stringify(imageList, null, 2)};
`;
    
    fs.writeFileSync(
      path.join(dataDir, 'static-images.js'),
      jsOutput
    );
    
    const compositesCount = imageList.filter(img => img.has_composite).length;
    console.log(`Generated list of ${imageList.length} images (${compositesCount} with side-by-side composites)`);
  } catch (error) {
    console.error('Error generating composite image list:', error);
  }
}

generateCompositeImageList();