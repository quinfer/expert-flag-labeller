// Upload ENNISKILLEN composite images first for testing
import { supabaseAdmin } from '../lib/supabase-admin.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function uploadEnniskillenComposites() {
  console.log('Starting upload of ENNISKILLEN composite images...');
  
  try {
    // Get source directory
    const sourceDir = path.join(__dirname, '../public/images/ENNISKILLEN');
    
    if (!fs.existsSync(sourceDir)) {
      console.error('Source directory does not exist:', sourceDir);
      return;
    }
    
    // Get all composite images from ENNISKILLEN
    const files = fs.readdirSync(sourceDir);
    const compositeFiles = files.filter(file => 
      file.startsWith('composite_') && file.endsWith('.jpg')
    );
    
    console.log(`Found ${compositeFiles.length} composite images in ENNISKILLEN`);
    
    let uploadedCount = 0;
    let errorCount = 0;
    
    for (const filename of compositeFiles) {
      try {
        const filePath = path.join(sourceDir, filename);
        const fileBuffer = fs.readFileSync(filePath);
        
        // Upload to Supabase Storage
        const { data, error } = await supabaseAdmin.storage
          .from('flag-images')
          .upload(`ENNISKILLEN/${filename}`, fileBuffer, {
            contentType: 'image/jpeg',
            upsert: true // Allow overwrite if exists
          });
        
        if (error) {
          if (error.message.includes('already exists')) {
            console.log(`Skipped existing: ${filename}`);
          } else {
            console.error(`Error uploading ${filename}:`, error.message);
            errorCount++;
          }
        } else {
          console.log(`Uploaded: ${filename}`);
          uploadedCount++;
        }
        
        // Add small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 100));
        
      } catch (fileError) {
        console.error(`Error processing ${filename}:`, fileError.message);
        errorCount++;
      }
    }
    
    console.log('\n=== Upload Summary ===');
    console.log(`Composite images found: ${compositeFiles.length}`);
    console.log(`Successfully uploaded: ${uploadedCount}`);
    console.log(`Errors: ${errorCount}`);
    console.log(`Total processed: ${uploadedCount + errorCount}`);
    
  } catch (error) {
    console.error('Script error:', error);
  }
}

// Run the upload
uploadEnniskillenComposites().catch(console.error); 