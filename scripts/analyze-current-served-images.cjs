const fs = require('fs');
const path = require('path');

// Load the currently served images
const staticImages = JSON.parse(fs.readFileSync('src/data/static-images.json', 'utf8'));

// Load the expert-confirmed dataset
const expertConfirmed = JSON.parse(fs.readFileSync('src/data/expert-confirmed-detailed.json', 'utf8'));

// Create a lookup set for expert-confirmed images
const expertConfirmedSet = new Set();
for (const [imageId, metadata] of Object.entries(expertConfirmed)) {
    expertConfirmedSet.add(imageId);
}

// Analyze the currently served images
let totalServed = 0;
let expertConfirmedServed = 0;
let falsePositivesServed = 0;
const townStats = {};

for (const imageObj of staticImages) {
    totalServed++;
    
    // Extract the image ID from the filename (remove _box0 suffix but keep .jpg extension)
    const imageId = imageObj.filename.replace('_box0.jpg', '.jpg');
    const town = imageObj.town;
    
    // Initialize town stats if not exists
    if (!townStats[town]) {
        townStats[town] = {
            total: 0,
            expertConfirmed: 0,
            falsePositives: 0
        };
    }
    
    townStats[town].total++;
    
    // Check if this image is in the expert-confirmed set
    if (expertConfirmedSet.has(imageId)) {
        expertConfirmedServed++;
        townStats[town].expertConfirmed++;
    } else {
        falsePositivesServed++;
        townStats[town].falsePositives++;
    }
}

// Calculate overall statistics
const falsePositiveRate = (falsePositivesServed / totalServed * 100).toFixed(2);
const expertConfirmedRate = (expertConfirmedServed / totalServed * 100).toFixed(2);

console.log('=== ANALYSIS OF CURRENTLY SERVED IMAGES ===\n');
console.log(`Total images currently served: ${totalServed.toLocaleString()}`);
console.log(`Expert-confirmed images served: ${expertConfirmedServed.toLocaleString()} (${expertConfirmedRate}%)`);
console.log(`False positives served: ${falsePositivesServed.toLocaleString()} (${falsePositiveRate}%)`);
console.log(`\nFalse positive rate: ${falsePositiveRate}%`);
console.log(`Expert-confirmed rate: ${expertConfirmedRate}%`);

// Sort towns by false positive count (descending)
const sortedTowns = Object.entries(townStats)
    .sort(([,a], [,b]) => b.falsePositives - a.falsePositives);

console.log('\n=== BREAKDOWN BY TOWN (Top 20 by false positives) ===');
console.log('Town'.padEnd(30) + 'Total'.padEnd(8) + 'Expert'.padEnd(8) + 'False+'.padEnd(8) + 'FP Rate');
console.log('-'.repeat(70));

for (const [town, stats] of sortedTowns.slice(0, 20)) {
    const fpRate = (stats.falsePositives / stats.total * 100).toFixed(1);
    console.log(
        town.padEnd(30) + 
        stats.total.toString().padEnd(8) + 
        stats.expertConfirmed.toString().padEnd(8) + 
        stats.falsePositives.toString().padEnd(8) + 
        fpRate + '%'
    );
}

// Show towns with highest false positive rates
console.log('\n=== TOWNS WITH HIGHEST FALSE POSITIVE RATES (>90%) ===');
const highFPTowns = sortedTowns.filter(([,stats]) => 
    stats.falsePositives / stats.total > 0.9 && stats.total > 10
);

if (highFPTowns.length > 0) {
    console.log('Town'.padEnd(30) + 'Total'.padEnd(8) + 'Expert'.padEnd(8) + 'False+'.padEnd(8) + 'FP Rate');
    console.log('-'.repeat(70));
    
    for (const [town, stats] of highFPTowns) {
        const fpRate = (stats.falsePositives / stats.total * 100).toFixed(1);
        console.log(
            town.padEnd(30) + 
            stats.total.toString().padEnd(8) + 
            stats.expertConfirmed.toString().padEnd(8) + 
            stats.falsePositives.toString().padEnd(8) + 
            fpRate + '%'
        );
    }
} else {
    console.log('No towns with >90% false positive rate found.');
}

// Show towns with best expert-confirmed rates
console.log('\n=== TOWNS WITH BEST EXPERT-CONFIRMED RATES (>50%) ===');
const highExpertTowns = sortedTowns.filter(([,stats]) => 
    stats.expertConfirmed / stats.total > 0.5 && stats.total > 10
).sort(([,a], [,b]) => (b.expertConfirmed/b.total) - (a.expertConfirmed/a.total));

if (highExpertTowns.length > 0) {
    console.log('Town'.padEnd(30) + 'Total'.padEnd(8) + 'Expert'.padEnd(8) + 'False+'.padEnd(8) + 'Expert Rate');
    console.log('-'.repeat(70));
    
    for (const [town, stats] of highExpertTowns.slice(0, 10)) {
        const expertRate = (stats.expertConfirmed / stats.total * 100).toFixed(1);
        console.log(
            town.padEnd(30) + 
            stats.total.toString().padEnd(8) + 
            stats.expertConfirmed.toString().padEnd(8) + 
            stats.falsePositives.toString().padEnd(8) + 
            expertRate + '%'
        );
    }
} else {
    console.log('No towns with >50% expert-confirmed rate found.');
}

console.log('\n=== SUMMARY ===');
console.log(`The current system is serving ${falsePositivesServed.toLocaleString()} false positives out of ${totalServed.toLocaleString()} total images.`);
console.log(`This represents a ${falsePositiveRate}% false positive rate in the currently served dataset.`);
console.log(`Only ${expertConfirmedRate}% of currently served images are expert-confirmed true positives.`); 