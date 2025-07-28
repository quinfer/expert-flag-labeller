import { supabaseAdmin } from '../lib/supabase-admin.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Helper function to extract base filename
function extractBaseFilename(filename) {
  if (filename.includes('_box') && filename.endsWith('.jpg')) {
    return filename.replace(/_box\d+\.jpg$/, '');
  }
  if (filename.startsWith('composite_')) {
    const withoutComposite = filename.replace('composite_', '');
    return withoutComposite.replace(/_box\d+\.jpg$/, '');
  }
  if (filename.endsWith('.jpg')) {
    return filename.replace('.jpg', '');
  }
  return filename;
}

async function createDisputedImagesPackage() {
  console.log('📦 CREATING DISPUTED IMAGES PACKAGE');
  console.log('=' .repeat(50));
  
  try {
    // Step 1: Get Barry's disputed classifications
    console.log('1️⃣ Loading Barry\'s disputed classifications...');
    const { data: barryReviewClassifications, error: barryError } = await supabaseAdmin
      .from('classifications')
      .select('*')
      .eq('expert_id', 'Barry')
      .eq('town', 'ENNISKILLEN')
      .eq('primary_category', 'Review')
      .order('timestamp', { ascending: true });
      
    if (barryError) {
      console.error('❌ Error fetching Barry\'s classifications:', barryError);
      return;
    }
    
    console.log(`   ✅ Found ${barryReviewClassifications?.length || 0} disputed images`);
    
    // Step 2: Load false positive data
    console.log('2️⃣ Loading false positive data...');
    
    const { execSync } = await import('child_process');
    
    // Run the Python script to create the data file
    execSync('python3 scripts/load_false_positive_data.py', { encoding: 'utf8' });
    
    // Read the JSON file
    const dataPath = path.join(__dirname, 'false_positive_data.json');
    const falsePositiveData = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
    
    console.log('   ✅ Loaded false positive and expert confirmation data');
    
    // Step 3: Create output directory
    const outputDir = path.join(__dirname, '..', 'disputed-images-analysis');
    const imagesDir = path.join(outputDir, 'images');
    
    if (fs.existsSync(outputDir)) {
      fs.rmSync(outputDir, { recursive: true });
    }
    fs.mkdirSync(outputDir, { recursive: true });
    fs.mkdirSync(imagesDir, { recursive: true });
    
    console.log('3️⃣ Setting up directory structure...');
    console.log(`   Output: ${outputDir}`);
    
    // Step 4: Get disputed base filenames
    console.log('4️⃣ Identifying disputed images...');
    const disputedBaseFilenames = barryReviewClassifications.map(c => extractBaseFilename(c.image_id));
    console.log(`   📋 Disputed base filenames: ${disputedBaseFilenames.length}`);
    
    // Step 5: Filter false positive data for disputed images
    console.log('5️⃣ Filtering false positive data...');
    const disputedFalsePositiveData = falsePositiveData.false_positive_data.filter(row => 
      disputedBaseFilenames.includes(row.f)
    );
    
    console.log(`   ✅ Found ${disputedFalsePositiveData.length} records for disputed images`);
    
    // Step 6: Create simple CSV with original pickle file data
    console.log('6️⃣ Writing CSV file...');
    
    if (disputedFalsePositiveData.length === 0) {
      console.error('❌ No disputed records found in false positive data');
      return;
    }
    
    const csvHeaders = Object.keys(disputedFalsePositiveData[0]);
    const csvContent = [
      csvHeaders.join(','),
      ...disputedFalsePositiveData.map(row => 
        csvHeaders.map(header => {
          const value = row[header];
          // Escape commas and quotes in CSV
          if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value;
        }).join(',')
      )
    ].join('\n');
    
    const csvPath = path.join(outputDir, 'disputed_images_pickle_data.csv');
    fs.writeFileSync(csvPath, csvContent);
    
    // Step 7: Copy images
    console.log('7️⃣ Copying images...');
    let copiedImages = 0;
    
    for (const [index, classification] of barryReviewClassifications.entries()) {
      const baseFilename = extractBaseFilename(classification.image_id);
      
      // Copy images
      const sourceImageDir = path.join(__dirname, '..', 'public', 'images', 'ENNISKILLEN');
      
      // Copy original panoramic image
      const originalFile = `${baseFilename}.jpg`;
      const originalSrc = path.join(sourceImageDir, originalFile);
      const originalDest = path.join(imagesDir, originalFile);
      
      if (fs.existsSync(originalSrc)) {
        fs.copyFileSync(originalSrc, originalDest);
        copiedImages++;
      }
      
      // Copy cropped version
      const croppedSrc = path.join(sourceImageDir, classification.image_id);
      const croppedDest = path.join(imagesDir, classification.image_id);
      
      if (fs.existsSync(croppedSrc)) {
        fs.copyFileSync(croppedSrc, croppedDest);
        copiedImages++;
      }
      
      // Copy expert confirmed version if available
      const expertSrc = path.join(__dirname, '..', 'flag_imagesCORRECT', `${baseFilename}.jpg`);
      const expertDest = path.join(imagesDir, `expert_confirmed_${baseFilename}.jpg`);
      
      if (fs.existsSync(expertSrc)) {
        fs.copyFileSync(expertSrc, expertDest);
        copiedImages++;
      }
    }
    
    // Step 8: Create summary JSON
    console.log('8️⃣ Creating summary JSON...');
    
    const summaryData = {
      metadata: {
        generated_at: new Date().toISOString(),
        total_disputed_images: disputedBaseFilenames.length,
        total_pickle_records: disputedFalsePositiveData.length,
        analysis_focus: 'Original pickle file data for disputed images',
        csv_columns: csvHeaders,
        expert_confirmed_count: disputedBaseFilenames.filter(f => falsePositiveData.expert_confirmed.includes(f)).length
      },
      disputed_images: disputedBaseFilenames,
      dataset_context: {
        total_images_processed: falsePositiveData.metadata.total_records,
        expert_confirmed_images: falsePositiveData.metadata.expert_confirmed_count,
        pickle_file_columns: falsePositiveData.metadata.columns
      },
      files_included: {
        csv_file: 'disputed_images_pickle_data.csv',
        images_folder: 'images/',
        total_images_copied: copiedImages
      }
    };
    
    const summaryPath = path.join(outputDir, 'summary.json');
    fs.writeFileSync(summaryPath, JSON.stringify(summaryData, null, 2));
    
    // Step 9: Create README
    console.log('9️⃣ Creating documentation...');
    
    const readmeContent = `# Disputed Images - Original Pickle File Data
## ENNISKILLEN False Positive Data for Barry's Disputed Images

### 📊 Overview
This package contains the original pickle file data (ENNISKILLENresultsCORRECT.pickle) filtered to show only the ${disputedBaseFilenames.length} images that Barry marked for review.

### 🔍 The Data
- **Source**: ENNISKILLENresultsCORRECT.pickle
- **Disputed Images**: ${disputedBaseFilenames.length} base filenames
- **CSV Records**: ${disputedFalsePositiveData.length} rows (includes different angles/crops of same panoramic images)
- **Columns**: ${csvHeaders.join(', ')}

### 📁 Package Contents

#### Files
- \`disputed_images_pickle_data.csv\` - Original pickle data for disputed images (${disputedFalsePositiveData.length} rows)
- \`summary.json\` - Metadata and statistics
- \`images/\` - All relevant image files (${copiedImages} images)
- \`README.md\` - This documentation

#### Image Types
For each disputed case, you'll find:
- \`[basename].jpg\` - Original panoramic street view
- \`[basename]_box0.jpg\` - Cropped flag region (Barry's focus)
- \`expert_confirmed_[basename].jpg\` - Expert-confirmed version (if available)

### 📋 CSV Structure
The CSV file contains the original pickle file columns:

| Column | Description |
|--------|-------------|
| f | Base filename (panoramic image identifier) |
| pano_id | Panoramic image ID |
| flags | Number of flags detected by CV |
| indicator | 1.0 = show to experts, NaN = don't show |
| flags_correct | Expert verification (1 = correct, 0 = incorrect) |

### 🎯 Key Insights
- All disputed images have \`indicator = 1.0\` (marked to show to experts)
- All disputed images have \`flags_correct = 1\` (experts confirmed as genuine flags)
- Barry flagged these ${disputedBaseFilenames.length} images as false positives despite expert confirmation

### 📈 Context
- Part of ${falsePositiveData.metadata.total_records} total images in pickle file
- ${falsePositiveData.metadata.expert_confirmed_count} images were expert-confirmed in total
- These ${disputedBaseFilenames.length} represent ${((disputedBaseFilenames.length / falsePositiveData.metadata.expert_confirmed_count) * 100).toFixed(1)}% of all expert-confirmed images

### 🔬 Analysis Usage
1. Load \`disputed_images_pickle_data.csv\` in your preferred analysis tool
2. Cross-reference with images in the \`images/\` folder
3. Compare Barry's field assessment with original expert confirmation
4. Identify patterns in disputed flag types or image characteristics

Generated: ${new Date().toISOString()}
`;

    fs.writeFileSync(path.join(outputDir, 'README.md'), readmeContent);
    
    console.log('✅ DISPUTED IMAGES PACKAGE COMPLETE!');
    console.log('=' .repeat(50));
    console.log(`📁 Package location: ${outputDir}`);
    console.log(`📊 Disputed base images: ${disputedBaseFilenames.length}`);
    console.log(`📋 CSV records: ${disputedFalsePositiveData.length}`);
    console.log(`🖼️ Images copied: ${copiedImages}`);
    console.log(`📄 CSV file: disputed_images_pickle_data.csv`);
    console.log(`📋 Summary: summary.json`);
    console.log();
    console.log('🔍 CSV COLUMNS:');
    console.log(`   ${csvHeaders.join(', ')}`);
    console.log();
    console.log('📂 Package ready for analysis!');
    
  } catch (error) {
    console.error('❌ Error creating disputed images package:', error);
  }
}

createDisputedImagesPackage().catch(console.error); 