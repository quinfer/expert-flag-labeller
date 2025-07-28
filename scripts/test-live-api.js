const fs = require('fs');

// Function to test the API endpoint
async function testAPI() {
    try {
        console.log('Testing the actual API endpoint...\n');
        
        // Test the images-static endpoint
        const response = await fetch('http://localhost:3000/api/images-static');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log('=== API RESPONSE ANALYSIS ===');
        console.log('Success:', data.success);
        console.log('Data source:', data.metadata?.source || 'unknown');
        console.log('Total images returned:', data.metadata?.total_images || data.images?.length || 0);
        
        if (data.metadata?.filtering) {
            const filtering = data.metadata.filtering;
            console.log('\n=== FILTERING STATISTICS ===');
            console.log('Filtering enabled:', filtering.enabled);
            console.log('Original count:', filtering.original_count);
            console.log('Filtered count:', filtering.filtered_count);
            console.log('Removed count:', filtering.removed_count);
            console.log('Removed percentage:', filtering.removed_percentage.toFixed(2) + '%');
            console.log('Total false positives in lookup:', filtering.total_false_positives);
            console.log('Total towns:', filtering.total_towns);
            console.log('Overall FP rate:', filtering.overall_fp_rate.toFixed(2) + '%');
        }
        
        // Sample some images to show what's being served
        if (data.images && data.images.length > 0) {
            console.log('\n=== SAMPLE IMAGES BEING SERVED ===');
            const sample = data.images.slice(0, 5);
            sample.forEach((img, index) => {
                console.log(`${index + 1}. ${img.filename} (${img.town})`);
            });
            
            console.log('\n=== TOWN DISTRIBUTION ===');
            const townCounts = {};
            data.images.forEach(img => {
                townCounts[img.town] = (townCounts[img.town] || 0) + 1;
            });
            
            const sortedTowns = Object.entries(townCounts)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 10);
            
            sortedTowns.forEach(([town, count]) => {
                console.log(`${town}: ${count} images`);
            });
        }
        
        // Compare with our expert-confirmed dataset
        const expertConfirmed = JSON.parse(fs.readFileSync('src/data/expert-confirmed-detailed.json', 'utf8'));
        const expertConfirmedSet = new Set(Object.keys(expertConfirmed));
        
        let expertConfirmedCount = 0;
        let falsePositiveCount = 0;
        
        if (data.images) {
            data.images.forEach(img => {
                const imageId = img.filename.replace('_box0.jpg', '.jpg');
                if (expertConfirmedSet.has(imageId)) {
                    expertConfirmedCount++;
                } else {
                    falsePositiveCount++;
                }
            });
        }
        
        console.log('\n=== EXPERT-CONFIRMED ANALYSIS ===');
        console.log('Expert-confirmed images:', expertConfirmedCount);
        console.log('False positives:', falsePositiveCount);
        console.log('Expert-confirmed rate:', ((expertConfirmedCount / (expertConfirmedCount + falsePositiveCount)) * 100).toFixed(2) + '%');
        
    } catch (error) {
        console.error('Error testing API:', error.message);
        
        // If API is not running, show what the static file contains
        console.log('\n=== FALLBACK: ANALYZING STATIC FILE ===');
        try {
            const staticImages = JSON.parse(fs.readFileSync('src/data/static-images.json', 'utf8'));
            console.log('Static images count:', staticImages.length);
            
            // Check false positive filter
            const falsePositives = JSON.parse(fs.readFileSync('src/data/false-positives-lookup-all.json', 'utf8'));
            console.log('False positives in lookup:', falsePositives.count);
            console.log('Overall FP rate:', falsePositives.metadata?.overall_fp_rate?.toFixed(2) + '%');
            
            // Simulate filtering
            const fpSet = new Set(falsePositives.false_positives);
            let filtered = 0;
            
            staticImages.forEach(img => {
                const imageId = img.filename.replace('_box0.jpg', '.jpg');
                if (!fpSet.has(imageId)) {
                    filtered++;
                }
            });
            
            console.log('After filtering:', filtered, 'images would remain');
            console.log('Filtering would remove:', staticImages.length - filtered, 'images');
            console.log('Removal rate:', (((staticImages.length - filtered) / staticImages.length) * 100).toFixed(2) + '%');
            
        } catch (fileError) {
            console.error('Error reading static files:', fileError.message);
        }
    }
}

testAPI(); 