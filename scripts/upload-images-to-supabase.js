// scripts/upload-images-to-supabase.js
import { supabaseAdmin } from '../lib/supabase-admin.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { glob } from 'glob';
import dotenv from 'dotenv';

// Get current directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Load environment variables
dotenv.config({ path: path.join(projectRoot, '.env.local') });

// Configuration
const BUCKET_NAME = process.env.NEXT_PUBLIC_STORAGE_BUCKET || 'flag-images';
const STATIC_DIR = path.join(projectRoot, 'public', 'static');
const IMAGE_BATCH_SIZE = 10; // Upload 10 images at a time

async function uploadImages() {
  console.log('Starting image upload to Supabase...');
  console.log(`Using bucket: ${BUCKET_NAME}`);
  console.log(`Source directory: ${STATIC_DIR}`);
  
  try {
    // Check if the bucket exists
    const { data: buckets } = await supabaseAdmin.storage.listBuckets();
    const bucketExists = buckets.some(bucket => bucket.name === BUCKET_NAME);
    
    if (!bucketExists) {
      console.log(`Creating bucket: ${BUCKET_NAME}`);
      await supabaseAdmin.storage.createBucket(BUCKET_NAME, {
        public: true
      });
    }
    
    // Get list of all town directories
    const townDirs = fs.readdirSync(STATIC_DIR).filter(
      dir => fs.statSync(path.join(STATIC_DIR, dir)).isDirectory()
    );
    
    console.log(`Found ${townDirs.length} towns to process`);
    
    let totalImages = 0;
    let uploadedImages = 0;
    let failedImages = 0;
    
    // Process each town
    for (const town of townDirs) {
      console.log(`Processing town: ${town}`);
      
      // Get all image paths for this town
      const imagePaths = glob.sync(path.join(STATIC_DIR, town, '*.jpg'));
      totalImages += imagePaths.length;
      
      console.log(`Found ${imagePaths.length} images in ${town}`);
      
      // Process in batches
      for (let i = 0; i < imagePaths.length; i += IMAGE_BATCH_SIZE) {
        const batch = imagePaths.slice(i, i + IMAGE_BATCH_SIZE);
        console.log(`Processing batch ${Math.floor(i/IMAGE_BATCH_SIZE) + 1} of ${Math.ceil(imagePaths.length/IMAGE_BATCH_SIZE)} for ${town}`);
        
        // Process each image in the batch
        const uploadPromises = batch.map(async (imagePath) => {
          const filename = path.basename(imagePath);
          const storagePath = `${town}/${filename}`;
          
          try {
            // Read file
            const fileBuffer = fs.readFileSync(imagePath);
            
            // Upload to Supabase
            const { data, error } = await supabaseAdmin.storage
              .from(BUCKET_NAME)
              .upload(storagePath, fileBuffer, {
                cacheControl: '3600',
                upsert: true,
                contentType: 'image/jpeg'
              });
            
            if (error) {
              console.error(`Error uploading ${storagePath}:`, error.message);
              failedImages++;
              return { success: false, path: storagePath, error: error.message };
            }
            
            uploadedImages++;
            return { success: true, path: storagePath };
          } catch (err) {
            console.error(`Error processing ${filename}:`, err.message);
            failedImages++;
            return { success: false, path: storagePath, error: err.message };
          }
        });
        
        // Wait for all uploads in batch to complete
        await Promise.all(uploadPromises);
        console.log(`Completed batch. Progress: ${uploadedImages}/${totalImages} images uploaded`);
      }
    }
    
    console.log('\n====== UPLOAD SUMMARY ======');
    console.log(`Total images: ${totalImages}`);
    console.log(`Successfully uploaded: ${uploadedImages}`);
    console.log(`Failed: ${failedImages}`);
    console.log('============================\n');
    
  } catch (error) {
    console.error('Error in upload process:', error.message);
  }
}

// Run the upload function
uploadImages().catch(console.error);