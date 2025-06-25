// scripts/populate-image-metadata.js
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
const QUEUE_FILE = path.join(projectRoot, 'data', 'classification_queue.json');
const BATCH_SIZE = 100;

async function populateMetadata() {
  console.log('Starting metadata population...');
  console.log(`Using classification queue: ${QUEUE_FILE}`);
  console.log(`Supabase URL: ${process.env.NEXT_PUBLIC_SUPABASE_URL}`);
  console.log(`Bucket name: ${BUCKET_NAME}`);
  
  try {
    // Check if queue file exists
    if (!fs.existsSync(QUEUE_FILE)) {
      console.error(`Classification queue file not found: ${QUEUE_FILE}`);
      return;
    }
    
    // Read classification queue
    const queueData = JSON.parse(fs.readFileSync(QUEUE_FILE, 'utf8'));
    console.log(`Found ${queueData.images.length} images in queue`);
    
    // Create image_metadata table if it doesn't exist
    try {
      await supabaseAdmin.rpc('create_image_metadata_if_not_exists');
    } catch (e) {
      console.log('Setting up image_metadata table...');
      // Create table via SQL if RPC not available
      const { error } = await supabaseAdmin.from('image_metadata').select('id').limit(1);
      if (error && error.code === '42P01') { // relation does not exist
        console.log('Creating image_metadata table...');
        const createTableResult = await supabaseAdmin.rpc('create_metadata_table');
        console.log('Table creation result:', createTableResult);
      }
    }
    
    let totalImages = queueData.images.length;
    let processedImages = 0;
    let failedImages = 0;
    
    // Process in batches
    for (let i = 0; i < queueData.images.length; i += BATCH_SIZE) {
      const batch = queueData.images.slice(i, i + BATCH_SIZE);
      console.log(`Processing batch ${Math.floor(i/BATCH_SIZE) + 1} of ${Math.ceil(queueData.images.length/BATCH_SIZE)}`);
      
      // Transform data for Supabase
      const metadataRecords = batch.map(img => {
        const town = img.town.toUpperCase().replace(/ /g, '_');
        const filename = img.filename || path.basename(img.path || '');
        
        // Determine if it's a composite or has composite
        const isComposite = filename.startsWith('composite_');
        const hasComposite = !!img.has_composite || !!img.composite_image || 
                            (filename.includes('_box') && !isComposite);
        
        // Calculate storage paths
        const storagePath = `${town}/${filename}`;
        let compositePath = null;
        
        // For images with composites, calculate the composite path
        if (hasComposite && !isComposite) {
          if (img.composite_image) {
            // Extract filename from composite path
            const compositeFilename = path.basename(img.composite_image);
            compositePath = `${town}/${compositeFilename}`;
          } else {
            // Generate composite path based on filename
            compositePath = `${town}/composite_${filename}`;
          }
        }
        
        return {
          town,
          filename,
          storage_path: storagePath,
          composite_path: compositePath,
          has_composite: hasComposite
        };
      });
      
      // Insert into Supabase
      const { data, error } = await supabaseAdmin
        .from('image_metadata')
        .upsert(metadataRecords, { 
          onConflict: 'town,filename',
          ignoreDuplicates: false
        });
        
      if (error) {
        console.error(`Error inserting batch ${i}:`, error.message);
        failedImages += batch.length;
      } else {
        processedImages += batch.length;
        console.log(`Inserted batch ${i} to ${i + batch.length - 1}`);
      }
    }
    
    console.log('\n====== METADATA SUMMARY ======');
    console.log(`Total images: ${totalImages}`);
    console.log(`Successfully processed: ${processedImages}`);
    console.log(`Failed: ${failedImages}`);
    console.log('==============================\n');
    
  } catch (error) {
    console.error('Error in metadata processing:', error.message);
  }
}

// Run the metadata population function
populateMetadata().catch(console.error);