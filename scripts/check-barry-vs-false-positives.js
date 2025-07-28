import { supabaseAdmin } from '../lib/supabase-admin.js';
import fs from 'fs';

// Helper function to extract base filename from various formats
function extractBaseFilename(filename) {
  // Handle composite images: composite_<base>_box<num>.jpg -> <base>
  if (filename.startsWith('composite_')) {
    const withoutComposite = filename.replace('composite_', '');
    const withoutBox = withoutComposite.replace(/_box\d+\.jpg$/, '');
    return withoutBox;
  }
  
  // Handle Barry's composite images: <base>_box<num>.jpg -> <base>
  if (filename.includes('_box') && filename.endsWith('.jpg')) {
    const withoutBox = filename.replace(/_box\d+\.jpg$/, '');
    return withoutBox;
  }
  
  // Handle regular images: <base>.jpg -> <base>
  if (filename.endsWith('.jpg')) {
    return filename.replace('.jpg', '');
  }
  
  // Return as-is if no known pattern
  return filename;
}

async function checkBarryVsFalsePositives() {
  console.log('🔍 CHECKING BARRY\'S CLASSIFICATIONS VS FALSE POSITIVE DATA');
  console.log('=' .repeat(70));
  console.log();
  
  try {
    // Step 1: Get Barry's classifications
    console.log('1️⃣ Loading Barry\'s classifications from database...');
    const { data: barryClassifications, error: barryError } = await supabaseAdmin
      .from('classifications')
      .select('*')
      .eq('expert_id', 'Barry')
      .eq('town', 'ENNISKILLEN')
      .order('timestamp', { ascending: true });
      
    if (barryError) {
      console.error('❌ Error fetching Barry\'s classifications:', barryError);
      return;
    }
    
    console.log(`   ✅ Found ${barryClassifications?.length || 0} Barry classifications for ENNISKILLEN`);
    
    if (!barryClassifications || barryClassifications.length === 0) {
      console.log('   ⚠️  No Barry classifications found for ENNISKILLEN');
      return;
    }
    
    // Step 2: Load false positive data
    console.log('\n2️⃣ Loading false positive data...');
    
    let falsePositiveData;
    try {
      // Use Python to load pickle file
      const { execSync } = await import('child_process');
      const pythonScript = `
import pickle
import pandas as pd
import json

# Load the corrected results file
df = pd.read_pickle('false_positive_checks/ENNISKILLENresultsCORRECT.pickle')

# Create lookup for false positives and true positives
false_positives = set(df[df['indicator'].isna()]['f'].tolist())
true_positives = set(df[df['indicator'] == '1.0']['f'].tolist())

# Output as JSON
result = {
  'false_positives': list(false_positives),
  'true_positives': list(true_positives),
  'total_records': len(df)
}

print(json.dumps(result))
      `;
      
      const pythonResult = execSync(`python3 -c "${pythonScript}"`, { encoding: 'utf8' });
      falsePositiveData = JSON.parse(pythonResult);
      
      console.log(`   ✅ Loaded false positive data:`);
      console.log(`      • False positives: ${falsePositiveData.false_positives.length}`);
      console.log(`      • True positives: ${falsePositiveData.true_positives.length}`);
      console.log(`      • Total records: ${falsePositiveData.total_records}`);
      
    } catch (error) {
      console.error('❌ Error loading false positive data:', error);
      return;
    }
    
    // Step 3: Analyze Barry's classifications
    console.log('\n3️⃣ Analyzing Barry\'s classifications...');
    
    const flaggedImages = [];
    const nonFlaggedImages = [];
    
    barryClassifications.forEach(classification => {
      const baseFilename = extractBaseFilename(classification.image_id);
      
      // Determine if Barry flagged this image
      const isFlagged = classification.primary_category && 
                       classification.primary_category !== 'No Flag' && 
                       classification.primary_category !== 'None';
      
      if (isFlagged) {
        flaggedImages.push({
          ...classification,
          baseFilename,
          category: classification.primary_category,
          specificFlag: classification.specific_flag
        });
      } else {
        nonFlaggedImages.push({
          ...classification,
          baseFilename
        });
      }
    });
    
    console.log(`   📊 Barry's classification breakdown:`);
    console.log(`      • Flagged images: ${flaggedImages.length}`);
    console.log(`      • Non-flagged images: ${nonFlaggedImages.length}`);
    console.log(`      • Total: ${barryClassifications.length}`);
    
    // Step 4: Find discrepancies
    console.log('\n4️⃣ Finding discrepancies...');
    
    const discrepancies = [];
    const agreements = [];
    
    // Check Barry's flagged images against false positive data
    flaggedImages.forEach(flaggedImage => {
      const { baseFilename, category, specificFlag, image_id, timestamp } = flaggedImage;
      
      if (falsePositiveData.false_positives.includes(baseFilename)) {
        // DISCREPANCY: Barry flagged it, but false positive data says it's a false positive
        discrepancies.push({
          type: 'BARRY_FLAGGED_FALSE_POSITIVE',
          image_id,
          baseFilename,
          barryCategory: category,
          barrySpecificFlag: specificFlag,
          timestamp,
          issue: 'Barry flagged this image, but false positive data indicates it should be filtered out'
        });
      } else if (falsePositiveData.true_positives.includes(baseFilename)) {
        // AGREEMENT: Both Barry and false positive data agree it has flags
        agreements.push({
          type: 'AGREEMENT_TRUE_POSITIVE',
          image_id,
          baseFilename,
          barryCategory: category
        });
      } else {
        // Unknown: Barry flagged it, but it's not in false positive data
        discrepancies.push({
          type: 'BARRY_FLAGGED_UNKNOWN',
          image_id,
          baseFilename,
          barryCategory: category,
          barrySpecificFlag: specificFlag,
          timestamp,
          issue: 'Barry flagged this image, but it\'s not in the false positive dataset'
        });
      }
    });
    
    // Check Barry's non-flagged images
    nonFlaggedImages.forEach(nonFlaggedImage => {
      const { baseFilename, image_id, timestamp } = nonFlaggedImage;
      
      if (falsePositiveData.true_positives.includes(baseFilename)) {
        // DISCREPANCY: Barry didn't flag it, but false positive data says it's a true positive
        discrepancies.push({
          type: 'BARRY_MISSED_TRUE_POSITIVE',
          image_id,
          baseFilename,
          timestamp,
          issue: 'Barry didn\'t flag this image, but false positive data indicates it contains flags'
        });
      } else if (falsePositiveData.false_positives.includes(baseFilename)) {
        // AGREEMENT: Both Barry and false positive data agree it has no flags
        agreements.push({
          type: 'AGREEMENT_FALSE_POSITIVE',
          image_id,
          baseFilename
        });
      }
    });
    
    // Step 5: Report results
    console.log('\n5️⃣ RESULTS SUMMARY');
    console.log('=' .repeat(50));
    
    console.log(`\n✅ AGREEMENTS: ${agreements.length}`);
    const agreementsByType = agreements.reduce((acc, item) => {
      acc[item.type] = (acc[item.type] || 0) + 1;
      return acc;
    }, {});
    Object.entries(agreementsByType).forEach(([type, count]) => {
      console.log(`   • ${type}: ${count}`);
    });
    
    console.log(`\n⚠️  DISCREPANCIES: ${discrepancies.length}`);
    if (discrepancies.length > 0) {
      console.log('\n🔍 DETAILED DISCREPANCIES:');
      console.log('-' .repeat(60));
      
      discrepancies.forEach((discrepancy, index) => {
        console.log(`\n${index + 1}. ${discrepancy.type}`);
        console.log(`   Image: ${discrepancy.image_id}`);
        console.log(`   Base: ${discrepancy.baseFilename}`);
        if (discrepancy.barryCategory) {
          console.log(`   Barry's Category: ${discrepancy.barryCategory}`);
        }
        if (discrepancy.barrySpecificFlag) {
          console.log(`   Barry's Flag: ${discrepancy.barrySpecificFlag}`);
        }
        if (discrepancy.timestamp) {
          console.log(`   Date: ${new Date(discrepancy.timestamp).toLocaleDateString()}`);
        }
        console.log(`   Issue: ${discrepancy.issue}`);
      });
    }
    
    // Step 6: Create expert review report
    console.log('\n6️⃣ Creating expert review report...');
    
    const reportData = {
      summary: {
        total_barry_classifications: barryClassifications.length,
        barry_flagged_images: flaggedImages.length,
        barry_non_flagged_images: nonFlaggedImages.length,
        agreements: agreements.length,
        discrepancies: discrepancies.length,
        generated_at: new Date().toISOString()
      },
      agreements: agreements,
      discrepancies: discrepancies,
      discrepancy_types: discrepancies.reduce((acc, item) => {
        acc[item.type] = (acc[item.type] || 0) + 1;
        return acc;
      }, {}),
      recommendations: [
        'Review each discrepancy with the original expert who created the false positive data',
        'Verify image quality and visibility of flags in disputed cases',
        'Consider that Barry may have seen flags that were missed in the original analysis',
        'Update false positive data if Barry\'s classifications are correct',
        'Implement quality control measures for future classifications'
      ]
    };
    
    // Save report
    const reportPath = 'scripts/barry-vs-false-positives-report.json';
    fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2));
    
    console.log(`   ✅ Expert review report saved to: ${reportPath}`);
    
    // Step 7: Final recommendations
    console.log('\n7️⃣ RECOMMENDATIONS');
    console.log('=' .repeat(50));
    
    if (discrepancies.length > 0) {
      console.log('🚨 ACTION REQUIRED:');
      console.log('   1. Review the saved report with the original false positive expert');
      console.log('   2. Manually inspect each discrepancy image');
      console.log('   3. Determine if Barry\'s classifications or false positive data is correct');
      console.log('   4. Update the false positive filter accordingly');
      console.log(`   5. Consider implementing quality control checks`);
    } else {
      console.log('✅ NO DISCREPANCIES FOUND:');
      console.log('   Barry\'s classifications align perfectly with false positive data');
      console.log('   The false positive filter can be confidently applied');
    }
    
    console.log('\n📊 CONFIDENCE ASSESSMENT:');
    const confidenceScore = agreements.length / (agreements.length + discrepancies.length) * 100;
    console.log(`   Agreement rate: ${confidenceScore.toFixed(1)}%`);
    
    if (confidenceScore >= 95) {
      console.log('   🟢 HIGH CONFIDENCE: False positive data is very reliable');
    } else if (confidenceScore >= 80) {
      console.log('   🟡 MEDIUM CONFIDENCE: Minor discrepancies need review');
    } else {
      console.log('   🔴 LOW CONFIDENCE: Significant discrepancies require expert review');
    }
    
  } catch (error) {
    console.error('❌ Error during analysis:', error);
  }
}

// Run the analysis
checkBarryVsFalsePositives().catch(console.error); 