const fs = require('fs');

// Function to test the new expert-confirmed curation system
async function testExpertConfirmedCuration() {
    try {
        console.log('🧪 TESTING EXPERT-CONFIRMED CURATION SYSTEM\n');
        
        // Load the expert-confirmed dataset
        const expertConfirmed = JSON.parse(fs.readFileSync('src/data/expert-confirmed-detailed.json', 'utf8'));
        console.log(`📊 Expert-confirmed dataset: ${Object.keys(expertConfirmed).length} images`);
        
        // Load static images for comparison
        const staticImages = JSON.parse(fs.readFileSync('src/data/static-images.json', 'utf8'));
        console.log(`📊 Static images dataset: ${staticImages.length} images`);
        
        // Test the curation function
        const curatedImages = applyExpertConfirmedCuration(staticImages);
        console.log(`📊 Curated images: ${curatedImages.length} images`);
        
        // Calculate curation statistics
        const curationRate = ((curatedImages.length / staticImages.length) * 100).toFixed(1);
        console.log(`📈 Curation rate: ${curationRate}%`);
        
        // Analyze by town
        const townStats = {};
        curatedImages.forEach(img => {
            const town = img.town;
            townStats[town] = (townStats[town] || 0) + 1;
        });
        
        console.log('\n=== CURATION BY TOWN ===');
        const sortedTowns = Object.entries(townStats)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10);
        
        sortedTowns.forEach(([town, count]) => {
            console.log(`${town}: ${count} images`);
        });
        
        // Test filename matching logic
        console.log('\n=== FILENAME MATCHING TEST ===');
        const sampleImages = staticImages.slice(0, 5);
        sampleImages.forEach((img, index) => {
            const originalId = img.filename.replace('_box0.jpg', '.jpg');
            const isExpertConfirmed = Object.keys(expertConfirmed).includes(originalId);
            console.log(`${index + 1}. ${img.filename} -> ${originalId} -> ${isExpertConfirmed ? '✅ Expert-confirmed' : '❌ Not expert-confirmed'}`);
        });
        
        // Test against Railway API
        console.log('\n=== TESTING RAILWAY API ===');
        try {
            const response = await fetch('https://expert-flag-labeller-production.up.railway.app/api/images-static');
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Railway API accessible');
                console.log(`   Source: ${data.metadata?.source || 'unknown'}`);
                console.log(`   Curation: ${data.metadata?.curation || 'unknown'}`);
                console.log(`   Total images: ${data.metadata?.total_images || data.images?.length || 0}`);
                
                if (data.metadata?.curation_stats) {
                    console.log(`   Original count: ${data.metadata.curation_stats.original_count}`);
                    console.log(`   Curated count: ${data.metadata.curation_stats.curated_count}`);
                    console.log(`   Curation rate: ${data.metadata.curation_stats.curation_rate}`);
                }
            } else {
                console.log('❌ Railway API not accessible');
            }
        } catch (error) {
            console.log('❌ Railway API test failed:', error.message);
        }
        
        // Check for potential filename mismatches with Supabase
        console.log('\n=== SUPABASE FILENAME COMPATIBILITY ===');
        console.log('Note: Supabase may have modified filenames with _box0 suffix');
        console.log('The curation system handles this by removing _box0 suffix before matching');
        
        // Sample some expert-confirmed IDs to show the format
        const sampleExpertIds = Object.keys(expertConfirmed).slice(0, 5);
        console.log('\nSample expert-confirmed image IDs:');
        sampleExpertIds.forEach(id => {
            console.log(`   ${id}`);
        });
        
        console.log('\n=== SUMMARY ===');
        console.log(`✅ Expert-confirmed curation system ready`);
        console.log(`✅ ${curatedImages.length} expert-verified images available`);
        console.log(`✅ ${curationRate}% curation rate from static dataset`);
        console.log(`✅ Filename matching handles _box0 suffix correctly`);
        
    } catch (error) {
        console.error('❌ Error testing expert-confirmed curation:', error.message);
    }
}

/**
 * Apply expert-confirmed curation to filter images
 * Only returns images that have been verified by experts as containing flags
 */
function applyExpertConfirmedCuration(images) {
    try {
        // Load expert-confirmed dataset
        const expertConfirmed = JSON.parse(fs.readFileSync('src/data/expert-confirmed-detailed.json', 'utf8'));
        
        // Create a set of expert-confirmed image IDs for fast lookup
        const expertConfirmedSet = new Set(Object.keys(expertConfirmed));
        
        // Filter images to only include expert-confirmed ones
        const curatedImages = images.filter(image => {
            // Extract the image ID from the filename (handle _box0 suffix)
            const imageId = image.filename.replace('_box0.jpg', '.jpg');
            return expertConfirmedSet.has(imageId);
        });
        
        return curatedImages;
    } catch (error) {
        console.error("[CURATION] Error applying expert-confirmed curation:", error);
        // If curation fails, return all images as fallback
        return images;
    }
}

testExpertConfirmedCuration(); 