// scripts/test-false-positive-filter.js
import { readFile } from 'fs/promises';
import { join } from 'path';

async function testFalsePositiveFilter() {
  console.log('🧪 Testing False Positive Filter System');
  console.log('='*50);
  
  try {
    // Load the false positive lookup data
    const fpLookupPath = join(process.cwd(), 'src/data/false-positives-lookup.json');
    const fpData = JSON.parse(await readFile(fpLookupPath, 'utf8'));
    
    console.log(`✅ Loaded false positive lookup: ${fpData.count} entries`);
    
    // Load static images for testing
    const staticImagesPath = join(process.cwd(), 'src/data/static-images.json');
    const staticImages = JSON.parse(await readFile(staticImagesPath, 'utf8'));
    
    console.log(`✅ Loaded static images: ${staticImages.length} entries`);
    
    // Test individual filename checking
    const testFilenames = [
      // Sample false positives from our data
      '--2A5w94q8bzpnU4kTt2yQ_000.jpg',
      '--2A5w94q8bzpnU4kTt2yQ_060.jpg',
      // Sample true positives from our data
      '-A082_08bAUscI8N6hKQRg_180.jpg',
      '-BiEXNkFswWNdrTXl0rsPg_180.jpg',
      // Non-existent file
      'nonexistent-file.jpg'
    ];
    
    console.log('\n🔍 Testing individual filenames:');
    testFilenames.forEach(filename => {
      const isFalsePositive = fpData.false_positives.includes(filename);
      const status = isFalsePositive ? '❌ FALSE POSITIVE' : '✅ TRUE POSITIVE';
      console.log(`   ${filename}: ${status}`);
    });
    
    // Test filtering static images
    console.log('\n🔄 Testing static image filtering:');
    const staticFilenames = staticImages.map(img => {
      const pathParts = img.path.split('/');
      return pathParts[pathParts.length - 1];
    });
    
    const falsePositiveSet = new Set(fpData.false_positives);
    const falsePositivesFound = staticFilenames.filter(filename => 
      falsePositiveSet.has(filename)
    );
    
    console.log(`   Static images total: ${staticImages.length}`);
    console.log(`   False positives found: ${falsePositivesFound.length}`);
    console.log(`   Images that would be filtered: ${falsePositivesFound.length}`);
    
    if (falsePositivesFound.length > 0) {
      console.log('   Sample false positives in static images:');
      falsePositivesFound.slice(0, 5).forEach((fp, i) => {
        console.log(`     ${i+1}. ${fp}`);
      });
    }
    
    // Test the API endpoint
    console.log('\n🌐 Testing API endpoint:');
    try {
      const response = await fetch('http://localhost:3000/api/images-static');
      const data = await response.json();
      
      if (data.success) {
        console.log(`✅ API returned ${data.images.length} images`);
        if (data.metadata.false_positive_filter) {
          console.log(`   Filter initialized: ${data.metadata.false_positive_filter.initialized}`);
          console.log(`   Filter entries: ${data.metadata.false_positive_filter.falsePositiveCount}`);
        }
        if (data.metadata.filtered_count !== undefined) {
          console.log(`   Original count: ${data.metadata.original_count}`);
          console.log(`   Filtered count: ${data.metadata.filtered_count}`);
        }
      } else {
        console.log('⚠️  API returned error:', data.error);
      }
    } catch (apiError) {
      console.log('⚠️  Could not test API (server may not be running):', apiError.message);
    }
    
    // Summary
    console.log('\n📊 SUMMARY:');
    console.log('='*50);
    console.log(`✅ False positive filter loaded: ${fpData.count} entries`);
    console.log(`✅ Static images loaded: ${staticImages.length} entries`);
    console.log(`✅ False positives in static images: ${falsePositivesFound.length}`);
    console.log(`✅ Filtering would remove: ${falsePositivesFound.length} images`);
    console.log(`✅ Final image count: ${staticImages.length - falsePositivesFound.length}`);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test
testFalsePositiveFilter().catch(console.error); 