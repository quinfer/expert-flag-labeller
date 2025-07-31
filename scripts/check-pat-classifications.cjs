#!/usr/bin/env node

/**
 * Check Pat's classification count and analyze progress restoration
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.local' });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Missing Supabase credentials in environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkPatClassifications() {
  try {
    console.log('🔍 Checking Pat\'s classifications...\n');

    // Get Pat's classifications
    const { data: patClassifications, error: patError } = await supabase
      .from('classifications')
      .select('*')
      .eq('expert_id', 'Pat');

    if (patError) {
      console.error('❌ Error fetching Pat\'s classifications:', patError);
      return;
    }

    console.log(`📊 Pat's Classification Summary:`);
    console.log(`   Total classifications: ${patClassifications.length}`);
    
    if (patClassifications.length > 0) {
      console.log(`   Sample image IDs: ${patClassifications.slice(0, 10).map(c => c.image_id).join(', ')}`);
    }

    // Get total images available for comparison
    const { data: allImages, error: imagesError } = await supabase
      .from('image_metadata')
      .select('filename', { count: 'exact', head: true });

    let totalImages = 0;
    if (!imagesError && allImages !== null) {
      // If image_metadata table exists, use that count
      const { count } = await supabase
        .from('image_metadata')
        .select('*', { count: 'exact', head: true });
      totalImages = count || 0;
      console.log(`   Total images in database: ${totalImages}`);
    } else {
      console.log('   📝 No image_metadata table found, app probably uses static images');
    }

    // Analyze Pat's image IDs vs expected formats
    if (patClassifications.length > 0) {
      console.log(`\n🔍 Pat's Image ID Analysis:`);
      const uniqueImageIds = new Set(patClassifications.map(c => c.image_id));
      console.log(`   Unique images classified: ${uniqueImageIds.size}`);
      
      // Sample some image IDs to see the format
      const sampleIds = Array.from(uniqueImageIds).slice(0, 10);
      console.log(`   Sample image IDs:`);
      sampleIds.forEach(id => console.log(`     - "${id}"`));
      
      // Check for patterns
      const compositeIds = Array.from(uniqueImageIds).filter(id => id.startsWith('composite_'));
      const regularIds = Array.from(uniqueImageIds).filter(id => !id.startsWith('composite_'));
      
      console.log(`   Regular image IDs: ${regularIds.length}`);
      console.log(`   Composite image IDs: ${compositeIds.length}`);
    }

    // Calculate what progress restoration algorithm would do
    console.log(`\n🧮 Progress Restoration Analysis:`);
    
    if (patClassifications.length === 0) {
      console.log('   Pat has no classifications - should start at image 0');
    } else {
      // This mimics the logic in the app
      const originalTotalImages = 5751; // From the app's proportional calculation
      const estimatedProgressPercent = Math.min(patClassifications.length / originalTotalImages, 1.0);
      
      console.log(`   If using proportional method:`);
      console.log(`     Classifications: ${patClassifications.length}`);
      console.log(`     Original total: ${originalTotalImages}`);
      console.log(`     Progress percent: ${(estimatedProgressPercent * 100).toFixed(1)}%`);
      
      if (totalImages > 0) {
        const calculatedIndex = Math.floor(estimatedProgressPercent * totalImages);
        console.log(`     Calculated index: ${calculatedIndex} of ${totalImages}`);
        
        if (calculatedIndex >= totalImages - 1) {
          console.log(`     ⚠️  ISSUE: This puts Pat at the last image!`);
        }
      }
    }

    console.log(`\n✅ Analysis complete!`);

  } catch (error) {
    console.error('❌ Script error:', error);
  }
}

// Run the analysis
checkPatClassifications();