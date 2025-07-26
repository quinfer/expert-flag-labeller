import { supabaseAdmin } from '../lib/supabase-admin.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Get current directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Load environment variables
dotenv.config({ path: path.join(projectRoot, '.env.local') });

// Configuration
const BUCKET_NAME = process.env.NEXT_PUBLIC_STORAGE_BUCKET || 'flag-images';

async function checkSupabaseStorage() {
  console.log('🔍 Checking Supabase storage contents...');
  console.log(`Bucket: ${BUCKET_NAME}\n`);
  
  try {
    // List all files in the bucket
    const { data: files, error } = await supabaseAdmin.storage
      .from(BUCKET_NAME)
      .list('', {
        limit: 1000,
        sortBy: { column: 'name', order: 'asc' }
      });
    
    if (error) {
      console.error('❌ Error listing bucket contents:', error.message);
      return;
    }
    
    console.log(`📁 Found ${files.length} items in bucket root`);
    
    // Get ENNISKILLEN files specifically
    const { data: enniskillenFiles, error: enniskillenError } = await supabaseAdmin.storage
      .from(BUCKET_NAME)
      .list('ENNISKILLEN', {
        limit: 1000,
        sortBy: { column: 'name', order: 'asc' }
      });
    
    if (enniskillenError) {
      console.error('❌ Error listing ENNISKILLEN files:', enniskillenError.message);
    } else {
      console.log(`\n🏴󠁧󠁢󠁮󠁩󠁲󠁿 ENNISKILLEN directory contains ${enniskillenFiles.length} files`);
      
      // Check for the specific missing files
      const missingFiles = [
        'composite_AM0Qj807DN2Cwz1ta8gHvA_060_box0.jpg',
        'composite_KJbo3q9uHfG8835TbhCeYw_180_box0.jpg', 
        'composite_WT8BKFK8pl3qno1oBROHCw_180_box0.jpg',
        'composite_7lRMzjfBfkZQ82uIc2MCbg_060_box0.jpg',
        'composite_AWWGrGcH4g8iKndJU7fXXw_120_box0.jpg'
      ];
      
      console.log('\n🔍 Checking for specific missing files:');
      missingFiles.forEach(filename => {
        const exists = enniskillenFiles.some(file => file.name === filename);
        console.log(`${exists ? '✅' : '❌'} ${filename}`);
      });
      
      // Count composite vs non-composite files
      const compositeFiles = enniskillenFiles.filter(file => file.name.startsWith('composite_'));
      const nonCompositeFiles = enniskillenFiles.filter(file => !file.name.startsWith('composite_'));
      
      console.log(`\n📊 ENNISKILLEN File Breakdown:`);
      console.log(`   🖼️  Composite files: ${compositeFiles.length}`);
      console.log(`   📸 Non-composite files: ${nonCompositeFiles.length}`);
      
      // Show first few composite files as examples
      console.log('\n📋 Sample composite files in storage:');
      compositeFiles.slice(0, 10).forEach(file => {
        console.log(`   ✅ ${file.name}`);
      });
      
      if (compositeFiles.length > 10) {
        console.log(`   ... and ${compositeFiles.length - 10} more`);
      }
    }
    
    // Now check what our data files expect
    console.log('\n📄 Checking data file references...');
    
    const staticImagesPath = path.join(projectRoot, 'src', 'data', 'static-images.json');
    if (fs.existsSync(staticImagesPath)) {
      const staticImages = JSON.parse(fs.readFileSync(staticImagesPath, 'utf8'));
      const enniskillenImages = staticImages.filter(img => img.town === 'ENNISKILLEN');
      const expectedComposites = enniskillenImages.filter(img => img.has_composite);
      
      console.log(`📊 Data file expectations:`);
      console.log(`   🏴󠁧󠁢󠁮󠁩󠁲󠁿 ENNISKILLEN images in data: ${enniskillenImages.length}`);
      console.log(`   🖼️  Expected composite images: ${expectedComposites.length}`);
      
      // Check which expected composites are missing
      console.log('\n🔍 Verifying expected composite images:');
      let missingCount = 0;
      expectedComposites.slice(0, 20).forEach(img => {
        if (img.composite_image) {
          const filename = img.composite_image.split('/').pop();
          const exists = enniskillenFiles && enniskillenFiles.some(file => file.name === filename);
          if (!exists) {
            console.log(`❌ Missing: ${filename}`);
            missingCount++;
          } else {
            console.log(`✅ Found: ${filename}`);
          }
        }
      });
      
      if (expectedComposites.length > 20) {
        console.log(`\n... checking remaining ${expectedComposites.length - 20} files...`);
        for (let i = 20; i < expectedComposites.length; i++) {
          const img = expectedComposites[i];
          if (img.composite_image) {
            const filename = img.composite_image.split('/').pop();
            const exists = enniskillenFiles && enniskillenFiles.some(file => file.name === filename);
            if (!exists) {
              missingCount++;
            }
          }
        }
      }
      
      console.log(`\n📊 Summary:`);
      console.log(`   📄 Expected composite files: ${expectedComposites.length}`);
      console.log(`   ✅ Found in storage: ${expectedComposites.length - missingCount}`);
      console.log(`   ❌ Missing from storage: ${missingCount}`);
      
      if (missingCount > 0) {
        const percentage = ((missingCount / expectedComposites.length) * 100).toFixed(1);
        console.log(`   📈 Missing percentage: ${percentage}%`);
      }
    }
    
  } catch (error) {
    console.error('💥 Error checking storage:', error.message);
  }
}

// Run the check
checkSupabaseStorage().catch(console.error); 