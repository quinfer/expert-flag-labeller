// scripts/upload-remaining-images.js
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
const IMAGES_DIR = path.join(projectRoot, 'public', 'images'); // Changed to images directory
const IMAGE_BATCH_SIZE = 10; // Upload 10 images at a time

async function uploadRemainingImages() {
  console.log('Starting upload of remaining images to Supabase...');
  console.log(`Using bucket: ${BUCKET_NAME}`);
  console.log(`Source directory: ${IMAGES_DIR}`);
  
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
    
    // Get list of already uploaded files from Supabase
    console.log('Checking existing files in Supabase...');
    const existingFiles = new Set();
    
    // Get list of all town directories
    const townDirs = fs.readdirSync(IMAGES_DIR).filter(
      dir => fs.statSync(path.join(IMAGES_DIR, dir)).isDirectory()
    );
    
    console.log(`Found ${townDirs.length} towns to process`);
    
    // Check what's already uploaded
    for (const town of townDirs) {
      const { data: files } = await supabaseAdmin.storage
        .from(BUCKET_NAME)
        .list(town, { limit: 1000 });
      
      if (files) {
        files.forEach(file => {
          existingFiles.add(`${town}/${file.name}`);
        });
      }
    }
    
    console.log(`Found ${existingFiles.size} files already in Supabase`);
    
    let totalImages = 0;
    let uploadedImages = 0;
    let skippedImages = 0;
    let failedImages = 0;
    
    // Process each town
    for (const town of townDirs) {
      console.log(`\nProcessing town: ${town}`);
      
      // Get all image paths for this town
      const imagePaths = glob.sync(path.join(IMAGES_DIR, town, '*.jpg'));
      const townImageCount = imagePaths.length;
      
      console.log(`Found ${townImageCount} images in ${town}`);
      
      // Filter out already uploaded images
      const imagesToUpload = imagePaths.filter(imagePath => {
        const filename = path.basename(imagePath);
        const storagePath = `${town}/${filename}`;
        return !existingFiles.has(storagePath);
      });
      
      const toUploadCount = imagesToUpload.length;
      const alreadyUploadedCount = townImageCount - toUploadCount;
      
      console.log(`Already uploaded: ${alreadyUploadedCount}, To upload: ${toUploadCount}`);
      
      if (toUploadCount === 0) {
        console.log(`All images already uploaded for ${town}, skipping...`);
        skippedImages += townImageCount;
        continue;
      }
      
      totalImages += toUploadCount;
      
      // Process in batches
      for (let i = 0; i < imagesToUpload.length; i += IMAGE_BATCH_SIZE) {
        const batch = imagesToUpload.slice(i, i + IMAGE_BATCH_SIZE);
        console.log(`Processing batch ${Math.floor(i/IMAGE_BATCH_SIZE) + 1} of ${Math.ceil(imagesToUpload.length/IMAGE_BATCH_SIZE)} for ${town}`);
        
        // Process each image in the batch
        const uploadPromises = batch.map(async (imagePath) => {
          const filename = path.basename(imagePath);
          const storagePath = `${town}/${filename}`;
          
          try {
            // Read file
            const fileData = fs.readFileSync(imagePath);
            
            // Upload to Supabase
            const { error } = await supabaseAdmin.storage
              .from(BUCKET_NAME)
              .upload(storagePath, fileData, {
                contentType: 'image/jpeg',
                upsert: false // Don't overwrite existing
              });
            
            if (error) {
              throw error;
            }
            
            uploadedImages++;
          } catch (error) {
            console.error(`Error processing ${filename}: ${error.message}`);
            failedImages++;
          }
        });
        
        // Wait for batch to complete
        await Promise.all(uploadPromises);
        console.log(`Completed batch. Progress: ${uploadedImages}/${totalImages} images uploaded`);
      }
    }
    
    console.log('\n====== UPLOAD SUMMARY ======');
    console.log(`Total new images to upload: ${totalImages}`);
    console.log(`Successfully uploaded: ${uploadedImages}`);
    console.log(`Already uploaded (skipped): ${skippedImages}`);
    console.log(`Failed: ${failedImages}`);
    console.log('============================');
    
  } catch (error) {
    console.error('Error during upload:', error);
  }
}

// Run the upload
uploadRemainingImages();