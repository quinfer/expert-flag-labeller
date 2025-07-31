#!/usr/bin/env node

/**
 * Debug Pat's progress restoration jumping to last image
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

async function debugPatProgressIssue() {
  try {
    console.log('🔍 Debugging Pat\'s progress restoration issue...\n');

    // Check all possible Pat identifications
    const patVariations = ['Pat', 'pat', 'Pat Quinn', 'PatQuinn', 'PATQUINN'];
    
    console.log('📋 Checking all possible Pat identifications:');
    
    for (const patId of patVariations) {
      const { data: classifications, error } = await supabase
        .from('classifications')
        .select('*')
        .eq('expert_id', patId);
      
      if (!error && classifications) {
        console.log(`   "${patId}": ${classifications.length} classifications`);
        if (classifications.length > 0) {
          console.log(`     Sample IDs: ${classifications.slice(0, 3).map(c => c.image_id).join(', ')}`);
        }
      }
    }

    // Check all expert_ids to see what exists
    console.log('\n👥 All expert_ids in database:');
    const { data: allExperts, error: expertsError } = await supabase
      .from('classifications')
      .select('expert_id')
      .limit(1000);
    
    if (!expertsError && allExperts) {
      const uniqueExperts = [...new Set(allExperts.map(c => c.expert_id))];
      console.log(`   Found experts: ${uniqueExperts.join(', ')}`);
      
      // Count classifications per expert
      for (const expertId of uniqueExperts) {
        const { data: expertClassifications, error: countError } = await supabase
          .from('classifications')
          .select('*', { count: 'exact', head: true })
          .eq('expert_id', expertId);
        
        if (!countError) {
          const { count } = await supabase
            .from('classifications')
            .select('*', { count: 'exact', head: true })
            .eq('expert_id', expertId);
          console.log(`     ${expertId}: ${count} classifications`);
        }
      }
    }

    // Simulate the progress restoration algorithm from the app
    console.log('\n🧮 Simulating Progress Restoration Algorithm:');
    
    // Get Pat's classifications (using exact 'Pat' as in login)
    const { data: patClassifications, error: patError } = await supabase
      .from('classifications')
      .select('*')
      .eq('expert_id', 'Pat');

    if (patError) {
      console.error('❌ Error:', patError);
      return;
    }

    console.log(`Step 1: Pat has ${patClassifications.length} classifications`);
    
    // Check if we can get the current image set
    let totalCurrentImages = 0;
    const { data: imageCheck, error: imageError } = await supabase
      .from('image_metadata')
      .select('*', { count: 'exact', head: true });
    
    if (!imageError && imageCheck !== null) {
      const { count } = await supabase
        .from('image_metadata')
        .select('*', { count: 'exact', head: true });
      totalCurrentImages = count || 0;
      console.log(`Step 2: Current image set has ${totalCurrentImages} images`);
    } else {
      // Fallback - simulate what the app would do with static images
      console.log('Step 2: No image_metadata table, app uses static images');
      // The app loads images from API - let's simulate typical count
      totalCurrentImages = 3344; // Typical curated count from memory
    }

    // Simulate the exact algorithm from page.tsx
    if (patClassifications.length === 0) {
      console.log('Step 3: No classifications found');
      console.log('Step 4: Should use exact filename matching (will find 0 matches)');
      console.log('Step 5: matchedCount = 0, so nextUnclassifiedIndex = 0');
      console.log('✅ Expected result: Pat should start at image 0');
    } else {
      console.log('Step 3: Has classifications, should check for exact matches');
      
      // The algorithm would look for exact filename matches first
      const classifiedImageIds = new Set(patClassifications.map(c => c.image_id));
      console.log(`Step 4: Looking for exact matches among ${classifiedImageIds.size} unique image IDs`);
      
      // If no matches found (which is likely with 0 classifications), it would use proportional
      if (patClassifications.length > 0) {
        const originalTotalImages = 5751; // From the app
        const estimatedProgressPercent = Math.min(patClassifications.length / originalTotalImages, 1.0);
        const calculatedIndex = Math.floor(estimatedProgressPercent * totalCurrentImages);
        
        console.log(`Step 5: Proportional calculation:`);
        console.log(`   ${patClassifications.length} ÷ ${originalTotalImages} = ${(estimatedProgressPercent * 100).toFixed(1)}%`);
        console.log(`   ${(estimatedProgressPercent * 100).toFixed(1)}% × ${totalCurrentImages} = index ${calculatedIndex}`);
        
        if (calculatedIndex >= totalCurrentImages - 10) {
          console.log(`🚨 FOUND THE BUG: This puts Pat at/near the last image!`);
        }
      }
    }

    // Check the robustness fix we added
    console.log('\n🛡️  Checking if robustness fix would help:');
    console.log('The robustness fix should check if the calculated image is already classified');
    console.log('Since Pat has 0 classifications, no images should be marked as classified');
    console.log('So the robustness fix should work correctly');

    // Final diagnosis
    console.log('\n🎯 DIAGNOSIS:');
    if (patClassifications.length === 0) {
      console.log('Pat has 0 classifications but is still jumping to last image');
      console.log('This suggests:');
      console.log('1. Bug in the progress restoration logic itself');
      console.log('2. Issue with how the app determines Pat has 0 classifications');
      console.log('3. Problem with the robustness fix implementation');
      console.log('4. Pat might have classifications under a different ID format');
    }

  } catch (error) {
    console.error('❌ Script error:', error);
  }
}

// Run the analysis
debugPatProgressIssue();