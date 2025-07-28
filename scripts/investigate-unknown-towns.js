// scripts/investigate-unknown-towns.js
import { supabaseAdmin } from '../lib/supabase-admin.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function investigateUnknownTowns() {
  console.log('🔍 Investigating UNKNOWN towns in classifications...\n');
  
  try {
    // 1. Check classifications with missing or null towns
    console.log('1️⃣ Checking classifications with missing/null towns...');
    const { data: classificationsMissingTowns, error: classError } = await supabaseAdmin
      .from('classifications')
      .select('*')
      .or('town.is.null,town.eq.""');
      
    if (classError) {
      console.error('Error fetching classifications:', classError);
    } else {
      console.log(`   Found ${classificationsMissingTowns?.length || 0} classifications with missing towns`);
      
      if (classificationsMissingTowns && classificationsMissingTowns.length > 0) {
        console.log('   🔍 Details:');
        classificationsMissingTowns.forEach((c, i) => {
          console.log(`      ${i + 1}. Image: ${c.image_id} | Town: "${c.town}" | Expert: ${c.expert_id} | Date: ${new Date(c.timestamp).toLocaleDateString()}`);
        });
      }
    }
    
    // 2. Check classifications with "UNKNOWN" town
    console.log('\n2️⃣ Checking classifications with "UNKNOWN" town...');
    const { data: classificationsUnknownTowns, error: unknownError } = await supabaseAdmin
      .from('classifications')
      .select('*')
      .eq('town', 'UNKNOWN');
      
    if (unknownError) {
      console.error('Error fetching UNKNOWN classifications:', unknownError);
    } else {
      console.log(`   Found ${classificationsUnknownTowns?.length || 0} classifications with "UNKNOWN" town`);
      
      if (classificationsUnknownTowns && classificationsUnknownTowns.length > 0) {
        console.log('   🔍 Details:');
        classificationsUnknownTowns.forEach((c, i) => {
          console.log(`      ${i + 1}. Image: ${c.image_id} | Expert: ${c.expert_id} | Date: ${new Date(c.timestamp).toLocaleDateString()}`);
        });
      }
    }
    
    // 3. Check if these images exist in the image_metadata table
    console.log('\n3️⃣ Checking image_metadata for town assignments...');
    const allProblematicImages = [
      ...(classificationsMissingTowns || []),
      ...(classificationsUnknownTowns || [])
    ];
    
    if (allProblematicImages.length > 0) {
      const imageIds = [...new Set(allProblematicImages.map(c => c.image_id))];
      console.log(`   Checking ${imageIds.length} unique images in image_metadata...`);
      
      for (const imageId of imageIds) {
        const { data: imageMetadata, error: metadataError } = await supabaseAdmin
          .from('image_metadata')
          .select('*')
          .eq('filename', imageId);
          
        if (metadataError) {
          console.error(`   Error checking ${imageId}:`, metadataError);
        } else if (imageMetadata && imageMetadata.length > 0) {
          const img = imageMetadata[0];
          console.log(`   📸 ${imageId}:`);
          console.log(`       Town in metadata: "${img.town}"`);
          console.log(`       Storage path: ${img.storage_path}`);
        } else {
          console.log(`   ❌ ${imageId}: NOT FOUND in image_metadata`);
        }
      }
    }
    
    // 4. Check static images data for completeness
    console.log('\n4️⃣ Checking static images data...');
    try {
      const fs = await import('fs');
      const staticImagesPath = 'src/data/static-images.json';
      
      if (fs.existsSync(staticImagesPath)) {
        const staticImagesData = JSON.parse(fs.readFileSync(staticImagesPath, 'utf8'));
        console.log(`   Static images file contains ${staticImagesData.length} entries`);
        
        // Check for missing towns in static data
        const missingTowns = staticImagesData.filter(img => !img.town || img.town === '');
        if (missingTowns.length > 0) {
          console.log(`   ❌ Found ${missingTowns.length} entries with missing towns in static data:`);
          missingTowns.slice(0, 5).forEach(img => {
            console.log(`       - ${img.filename}: town="${img.town}"`);
          });
          if (missingTowns.length > 5) {
            console.log(`       ... and ${missingTowns.length - 5} more`);
          }
        }
      } else {
        console.log('   ❌ Static images file not found');
      }
    } catch (error) {
      console.error('   Error checking static images:', error);
    }
    
    // 5. Check all towns in classifications
    console.log('\n5️⃣ All towns found in classifications:');
    const { data: allClassifications, error: allError } = await supabaseAdmin
      .from('classifications')
      .select('town');
      
    if (allError) {
      console.error('Error fetching all classifications:', allError);
    } else {
      const towns = [...new Set(allClassifications.map(c => c.town))];
      console.log(`   Found ${towns.length} unique towns:`);
      towns.sort().forEach(town => {
        const count = allClassifications.filter(c => c.town === town).length;
        console.log(`       - "${town}": ${count} classifications`);
      });
    }
    
  } catch (error) {
    console.error('❌ Error during investigation:', error);
  }
}

// Run the investigation
investigateUnknownTowns()
  .then(() => {
    console.log('\n✅ Investigation completed');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Investigation failed:', error);
    process.exit(1);
  }); 