// scripts/check-barry-detailed.js
import { supabaseAdmin } from '../lib/supabase-admin.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function checkBarryDetailed() {
  console.log('🔍 Checking Barry\'s detailed classification history...\n');
  
  try {
    // Get all classifications for Barry
    const { data: classifications, error } = await supabaseAdmin
      .from('classifications')
      .select('*')
      .eq('expert_id', 'Barry')
      .order('timestamp', { ascending: true });
      
    if (error) {
      console.error('Error fetching classifications:', error);
      return;
    }
    
    if (!classifications || classifications.length === 0) {
      console.log('No classifications found for Barry.');
      return;
    }
    
    console.log(`📊 Found ${classifications.length} classifications for Barry\n`);
    
    // Group by town
    const townGroups = {};
    classifications.forEach(classification => {
      const town = classification.town || 'UNKNOWN';
      if (!townGroups[town]) {
        townGroups[town] = [];
      }
      townGroups[town].push(classification);
    });
    
    console.log('🏘️  DETAILED BREAKDOWN BY TOWN:\n');
    console.log('='.repeat(80));
    
    Object.entries(townGroups).forEach(([town, townClassifications]) => {
      console.log(`\n📍 ${town} (${townClassifications.length} classifications):`);
      console.log('-'.repeat(50));
      
      townClassifications.forEach((classification, index) => {
        const date = new Date(classification.timestamp).toLocaleDateString();
        const time = new Date(classification.timestamp).toLocaleTimeString();
        
        console.log(`${index + 1}. Image: ${classification.image_id}`);
        console.log(`   🗓️  ${date} at ${time}`);
        console.log(`   🏷️  Category: ${classification.primary_category || 'N/A'}`);
        console.log(`   🎯 Flag: ${classification.specific_flag || 'N/A'}`);
        console.log(`   📝 Confidence: ${classification.confidence || 'N/A'}`);
        console.log(`   🚩 Needs Review: ${classification.needs_review || false}`);
        console.log(`   📋 ID: ${classification.id}`);
        console.log();
      });
    });
    
    console.log('='.repeat(80));
    console.log('\n📊 SUMMARY FOR BARRY:');
    console.log(`   Total Classifications: ${classifications.length}`);
    console.log(`   Towns: ${Object.keys(townGroups).join(', ')}`);
    console.log(`   Date Range: ${new Date(classifications[0].timestamp).toLocaleDateString()} to ${new Date(classifications[classifications.length - 1].timestamp).toLocaleDateString()}`);
    
    // Check for potential duplicates
    const imageIds = classifications.map(c => c.image_id);
    const uniqueImageIds = [...new Set(imageIds)];
    const duplicateCount = imageIds.length - uniqueImageIds.length;
    
    if (duplicateCount > 0) {
      console.log(`\n⚠️  WARNING: Found ${duplicateCount} potential duplicate classifications!`);
      
      // Show duplicates
      const duplicates = {};
      imageIds.forEach(id => {
        duplicates[id] = (duplicates[id] || 0) + 1;
      });
      
      console.log('\n🔍 DUPLICATE IMAGES:');
      Object.entries(duplicates).forEach(([imageId, count]) => {
        if (count > 1) {
          console.log(`   - ${imageId}: ${count} times`);
        }
      });
    }
    
  } catch (error) {
    console.error('Error checking Barry\'s classifications:', error);
  }
}

// Run the check
checkBarryDetailed()
  .then(() => {
    console.log('\n✅ Detailed check completed');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Detailed check failed:', error);
    process.exit(1);
  }); 