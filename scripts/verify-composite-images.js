// Verify that composite images exist for all multi-box cropped images
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import ProgressBar from 'progress';

// Get current directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Source directories
const staticDir = path.join(projectRoot, 'public', 'static');
const imagesDir = path.join(projectRoot, 'public', 'images');
const dataDir = path.join(projectRoot, 'data');

// Path to the classification queue JSON files
const queueFiles = fs.readdirSync(dataDir)
  .filter(file => file.startsWith('classification_queue_') && file.endsWith('.json'))
  .map(file => path.join(dataDir, file));

console.log(`Found ${queueFiles.length} classification queue files`);

// Statistics
const stats = {
  totalMultiBoxImages: 0,
  missingComposites: 0,
  hasComposites: 0,
  towns: {}
};

// Create a progress bar for processing queue files
const queueBar = new ProgressBar('Processing queue files [:bar] :current/:total :percent :etas', {
  complete: '=',
  incomplete: ' ',
  width: 30,
  total: queueFiles.length
});

// Process each queue file
queueFiles.forEach(queueFile => {
  try {
    const townName = path.basename(queueFile, '.json').replace('classification_queue_', '');
    queueBar.tick({town: townName});
    
    // Initialize town stats
    stats.towns[townName] = {
      totalMultiBoxImages: 0,
      missingComposites: 0,
      hasComposites: 0
    };
    
    // Read and parse the queue file
    const queueData = JSON.parse(fs.readFileSync(queueFile, 'utf8'));
    
    if (!queueData || !queueData.images || !Array.isArray(queueData.images)) {
      console.error(`Invalid queue file format: ${queueFile}`);
      return;
    }
    
    // Find all images that should have composites
    // This includes both multi-box cropped images AND boxed images
    const imagesToCheck = queueData.images.filter(item => {
      const filename = item.filename || '';
      return filename.match(/_box\d+\.jpg$/) || filename.includes('_boxed');
    });
    
    // Update stats without logging each individual entry
    stats.totalMultiBoxImages += imagesToCheck.length;
    stats.towns[townName].totalMultiBoxImages = imagesToCheck.length;
    
    // Create a progress bar for checking images in this town
    const imageBar = new ProgressBar(`  Checking ${townName} [:bar] :current/:total :percent`, {
      complete: '=',
      incomplete: ' ',
      width: 20,
      total: imagesToCheck.length,
      clear: true
    });
    
    // Store missing composites in an array to log later
    const missingComposites = [];
    
    // Check if composite images exist for each image
    imagesToCheck.forEach(item => {
      const filename = item.filename;
      const compositeFilename = `composite_${filename}`;
      const staticPath = path.join(staticDir, townName, compositeFilename);
      const imagesPath = path.join(imagesDir, townName, compositeFilename);
      
      const hasStaticComposite = fs.existsSync(staticPath);
      const hasImagesComposite = fs.existsSync(imagesPath);
      
      if (hasStaticComposite || hasImagesComposite) {
        stats.hasComposites++;
        stats.towns[townName].hasComposites++;
      } else {
        missingComposites.push(filename);
        stats.missingComposites++;
        stats.towns[townName].missingComposites++;
      }
      
      imageBar.tick();
    });
    
    // Log summary for this town
    if (missingComposites.length > 0) {
      console.log(`Found ${imagesToCheck.length} images that need composites in ${townName}`);
      console.log(`Missing ${missingComposites.length} composites in ${townName}`);
      
      // Only log the first 5 missing composites to avoid flooding the console
      if (missingComposites.length > 5) {
        console.log(`First 5 missing composites: ${missingComposites.slice(0, 5).join(", ")}...`);
      } else {
        console.log(`Missing composites: ${missingComposites.join(", ")}`);
      }
    }
  } catch (error) {
    console.error(`Error processing ${queueFile}:`, error);
  }
});

// Print statistics
console.log('\n===== COMPOSITE IMAGE VERIFICATION REPORT =====');
console.log(`Total Images Needing Composites: ${stats.totalMultiBoxImages}`);
console.log(`Images with Composites: ${stats.hasComposites} (${(stats.hasComposites / stats.totalMultiBoxImages * 100).toFixed(1)}%)`);
console.log(`Missing Composites: ${stats.missingComposites} (${(stats.missingComposites / stats.totalMultiBoxImages * 100).toFixed(1)}%)`);

console.log('\n===== PER-TOWN STATISTICS =====');
Object.entries(stats.towns).forEach(([town, townStats]) => {
  if (townStats.totalMultiBoxImages > 0) {
    const coveragePercent = (townStats.hasComposites / townStats.totalMultiBoxImages * 100).toFixed(1);
    console.log(`${town}: ${townStats.hasComposites}/${townStats.totalMultiBoxImages} (${coveragePercent}%)`);
  }
});

// Generate instructions for fixing missing composites
if (stats.missingComposites > 0) {
  console.log('\n===== RECOMMENDATIONS =====');
  console.log('To fix missing composite images, run:');
  console.log('1. Ensure you have run with the --side-by-side option:');
  console.log('   python scripts/prepare_images_for_classification.py --side-by-side --copy-to-public');
  console.log('2. Run the copy-to-static script to ensure all composites are transferred:');
  console.log('   node scripts/copy-images-to-static.js');
  console.log('3. Restart the application:');
  console.log('   npm run dev');
}