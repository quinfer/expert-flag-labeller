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
const STATIC_IMAGES_JSON = path.join(projectRoot, 'src', 'data', 'static-images.json');

/**
 * Get all files currently in Supabase Storage
 */
async function getSupabaseFiles() {
    console.log('📋 Fetching all files from Supabase Storage...');
    
    try {
        const { data: files, error } = await supabaseAdmin.storage
            .from(BUCKET_NAME)
            .list('', {
                limit: 20000,
                sortBy: { column: 'name', order: 'asc' }
            });

        if (error) {
            console.error('Error listing files:', error);
            return [];
        }

        // Get files from all subdirectories (towns)
        const allFiles = [];
        
        // Get all town directories
        const towns = files.filter(item => !item.name.includes('.'));
        
        for (const town of towns) {
            console.log(`  Checking town: ${town.name}`);
            
            const { data: townFiles, error: townError } = await supabaseAdmin.storage
                .from(BUCKET_NAME)
                .list(town.name, {
                    limit: 1000,
                    sortBy: { column: 'name', order: 'asc' }
                });

            if (townError) {
                console.error(`Error listing files for ${town.name}:`, townError);
                continue;
            }

            // Add full paths
            const fullPaths = townFiles.map(file => `${town.name}/${file.name}`);
            allFiles.push(...fullPaths);
        }

        console.log(`📊 Found ${allFiles.length} total files in Supabase Storage`);
        return allFiles;

    } catch (error) {
        console.error('Error fetching Supabase files:', error);
        return [];
    }
}

/**
 * Get required images from static-images.json
 */
function getRequiredImages() {
    console.log('📖 Loading required images from static-images.json...');
    
    try {
        const staticImagesData = fs.readFileSync(STATIC_IMAGES_JSON, 'utf8');
        const staticImages = JSON.parse(staticImagesData);
        
        const requiredFiles = new Set();
        
        staticImages.forEach(image => {
            // Add regular image path
            if (image.path) {
                requiredFiles.add(image.path);
            }
            
            // Add composite image path
            if (image.composite_image) {
                requiredFiles.add(image.composite_image);
            }
        });

        console.log(`📊 App requires ${requiredFiles.size} total image files`);
        console.log(`📊 From ${staticImages.length} image entries`);
        
        return Array.from(requiredFiles);

    } catch (error) {
        console.error('Error reading static-images.json:', error);
        return [];
    }
}

/**
 * Delete unused files from Supabase Storage
 */
async function deleteUnusedFiles(unusedFiles) {
    if (unusedFiles.length === 0) {
        console.log('✅ No unused files to delete!');
        return;
    }

    console.log(`🗑️  Deleting ${unusedFiles.length} unused files...`);
    
    let deletedCount = 0;
    let errorCount = 0;
    
    // Delete in batches to avoid overwhelming the API
    const BATCH_SIZE = 50;
    
    for (let i = 0; i < unusedFiles.length; i += BATCH_SIZE) {
        const batch = unusedFiles.slice(i, i + BATCH_SIZE);
        
        console.log(`🗑️  Deleting batch ${Math.floor(i / BATCH_SIZE) + 1}/${Math.ceil(unusedFiles.length / BATCH_SIZE)} (${batch.length} files)`);
        
        try {
            const { data, error } = await supabaseAdmin.storage
                .from(BUCKET_NAME)
                .remove(batch);

            if (error) {
                console.error('Batch delete error:', error);
                errorCount += batch.length;
            } else {
                deletedCount += batch.length;
                console.log(`✅ Successfully deleted ${batch.length} files in this batch`);
            }

        } catch (error) {
            console.error('Error deleting batch:', error);
            errorCount += batch.length;
        }

        // Small delay between batches
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    console.log('\n📊 Cleanup Summary:');
    console.log(`✅ Successfully deleted: ${deletedCount} files`);
    console.log(`❌ Failed to delete: ${errorCount} files`);
    console.log(`💰 Storage space freed up by removing ${deletedCount} unused images!`);
}

/**
 * Main cleanup function
 */
async function cleanupUnusedImages() {
    console.log('🧹 Starting Supabase Storage cleanup...\n');
    
    try {
        // Get current files in Supabase
        const supabaseFiles = await getSupabaseFiles();
        
        // Get required files from app
        const requiredFiles = getRequiredImages();
        
        if (supabaseFiles.length === 0 || requiredFiles.length === 0) {
            console.error('❌ Failed to load files. Cannot proceed with cleanup.');
            process.exit(1);
        }

        // Find unused files (in Supabase but not required by app)
        const requiredSet = new Set(requiredFiles);
        const unusedFiles = supabaseFiles.filter(file => !requiredSet.has(file));
        
        console.log('\n📊 Cleanup Analysis:');
        console.log(`📁 Files in Supabase Storage: ${supabaseFiles.length}`);
        console.log(`🎯 Files required by app: ${requiredFiles.length}`);
        console.log(`🗑️  Unused files to delete: ${unusedFiles.length}`);
        
        if (unusedFiles.length > 0) {
            console.log('\n🔍 Sample unused files:');
            unusedFiles.slice(0, 10).forEach(file => {
                console.log(`  - ${file}`);
            });
            if (unusedFiles.length > 10) {
                console.log(`  ... and ${unusedFiles.length - 10} more`);
            }
        }
        
        // Confirm before deleting
        console.log(`\n⚠️  This will DELETE ${unusedFiles.length} unused images from Supabase Storage.`);
        console.log('💡 Make sure your image uploads are complete before running this cleanup.');
        console.log('\n🚀 Starting deletion in 5 seconds... (Press Ctrl+C to cancel)');
        
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // Delete unused files
        await deleteUnusedFiles(unusedFiles);
        
        console.log('\n✅ Cleanup completed successfully!');
        
    } catch (error) {
        console.error('❌ Cleanup failed:', error);
        process.exit(1);
    }
}

// Run the cleanup
cleanupUnusedImages(); 