import { supabaseAdmin } from '../lib/supabase-admin.js';
import fs from 'fs';

// Helper function to extract base filename from composite images
function extractBaseFilename(filename) {
  // Handle Barry's composite images: <base>_box<num>.jpg -> <base>
  if (filename.includes('_box') && filename.endsWith('.jpg')) {
    const withoutBox = filename.replace(/_box\d+\.jpg$/, '');
    return withoutBox;
  }
  
  // Handle composite images: composite_<base>_box<num>.jpg -> <base>
  if (filename.startsWith('composite_')) {
    const withoutComposite = filename.replace('composite_', '');
    const withoutBox = withoutComposite.replace(/_box\d+\.jpg$/, '');
    return withoutBox;
  }
  
  // Handle regular images: <base>.jpg -> <base>
  if (filename.endsWith('.jpg')) {
    return filename.replace('.jpg', '');
  }
  
  return filename;
}

async function checkBarryReviewVsFalsePositives() {
  console.log('🔍 CHECKING BARRY\'S "FLAG FOR REVIEW" VS FALSE POSITIVE DATA');
  console.log('=' .repeat(70));
  console.log();
  console.log('Focus: Identifying potential discrepancies where Barry flagged');
  console.log('images for review but false positive data says they\'re true positives');
  console.log();
  
  try {
    // Step 1: Get Barry's "Review" classifications specifically
    console.log('1️⃣ Loading Barry\'s "flag for review" classifications...');
    const { data: barryReviewClassifications, error: barryError } = await supabaseAdmin
      .from('classifications')
      .select('*')
      .eq('expert_id', 'Barry')
      .eq('town', 'ENNISKILLEN')
      .eq('primary_category', 'Review')
      .order('timestamp', { ascending: true });
      
    if (barryError) {
      console.error('❌ Error fetching Barry\'s review classifications:', barryError);
      return;
    }
    
    console.log(`   ✅ Found ${barryReviewClassifications?.length || 0} "Review" classifications by Barry`);
    
    if (!barryReviewClassifications || barryReviewClassifications.length === 0) {
      console.log('   ℹ️  No "Review" classifications found. Barry hasn\'t flagged any images for review.');
      return;
    }
    
    // Step 2: Load false positive data
    console.log('\n2️⃣ Loading false positive data...');
    
    let falsePositiveData;
    try {
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
      
    } catch (error) {
      console.error('❌ Error loading false positive data:', error);
      return;
    }
    
    // Step 3: Analyze Barry's review classifications
    console.log('\n3️⃣ Analyzing Barry\'s "flag for review" classifications...');
    
    const discrepancies = [];
    const agreements = [];
    const unknowns = [];
    
    barryReviewClassifications.forEach(classification => {
      const baseFilename = extractBaseFilename(classification.image_id);
      const { image_id, timestamp, review_reason } = classification;
      
      console.log(`   🔍 Checking: ${image_id} (base: ${baseFilename})`);
      
      if (falsePositiveData.true_positives.includes(baseFilename)) {
        // DISCREPANCY: Barry flagged for review (suspects false positive), 
        // but false positive data says it's a true positive
        discrepancies.push({
          type: 'BARRY_REVIEW_VS_TRUE_POSITIVE',
          image_id,
          baseFilename,
          timestamp,
          review_reason,
          issue: 'Barry flagged this for review (suspected false positive), but false positive data indicates it contains genuine flags'
        });
        console.log(`     ⚠️  DISCREPANCY: Barry thinks false positive, data says true positive`);
      } else if (falsePositiveData.false_positives.includes(baseFilename)) {
        // AGREEMENT: Barry flagged for review and false positive data agrees it's a false positive
        agreements.push({
          type: 'BARRY_REVIEW_AGREES_FALSE_POSITIVE',
          image_id,
          baseFilename,
          timestamp,
          review_reason
        });
        console.log(`     ✅ AGREEMENT: Both Barry and data agree it's a false positive`);
      } else {
        // UNKNOWN: Barry flagged for review but it's not in false positive dataset
        unknowns.push({
          type: 'BARRY_REVIEW_UNKNOWN',
          image_id,
          baseFilename,
          timestamp,
          review_reason,
          issue: 'Barry flagged for review but image not found in false positive dataset'
        });
        console.log(`     ❓ UNKNOWN: Not found in false positive dataset`);
      }
    });
    
    // Step 4: Report results
    console.log('\n4️⃣ DETAILED RESULTS');
    console.log('=' .repeat(50));
    
    console.log(`\n📊 SUMMARY:`);
    console.log(`   • Total Barry "Review" classifications: ${barryReviewClassifications.length}`);
    console.log(`   • Agreements (Barry & data both say false positive): ${agreements.length}`);
    console.log(`   • Discrepancies (Barry says false positive, data says true positive): ${discrepancies.length}`);
    console.log(`   • Unknown (not in false positive dataset): ${unknowns.length}`);
    
    // Focus on discrepancies - these need manual inspection
    if (discrepancies.length > 0) {
      console.log('\n🚨 CRITICAL DISCREPANCIES REQUIRING MANUAL INSPECTION:');
      console.log('-' .repeat(60));
      console.log('These images need careful review by the original false positive expert:');
      console.log();
      
      discrepancies.forEach((discrepancy, index) => {
        console.log(`${index + 1}. Image: ${discrepancy.image_id}`);
        console.log(`   Base filename: ${discrepancy.baseFilename}`);
        console.log(`   Date Barry flagged: ${new Date(discrepancy.timestamp).toLocaleDateString()}`);
        console.log(`   Barry's reason: ${discrepancy.review_reason || 'Not specified'}`);
        console.log(`   ⚠️  Conflict: Barry suspects false positive, but analysis says true positive`);
        console.log(`   📝 Action: Manual inspection needed to determine who is correct`);
        console.log();
      });
      
      console.log('🔍 RECOMMENDED INSPECTION PROCESS:');
      console.log('   1. Manually examine each discrepancy image');
      console.log('   2. Determine if flags are genuinely visible and classifiable');
      console.log('   3. If Barry is correct: update false positive data');
      console.log('   4. If false positive data is correct: provide feedback to Barry');
      console.log('   5. Document decisions for future quality control');
    }
    
    // Show agreements for completeness
    if (agreements.length > 0) {
      console.log('\n✅ AGREEMENTS (Barry & false positive data both say false positive):');
      console.log('-' .repeat(60));
      
      agreements.forEach((agreement, index) => {
        console.log(`${index + 1}. ${agreement.image_id} (${agreement.baseFilename})`);
        console.log(`   Reason: ${agreement.review_reason || 'Not specified'}`);
      });
    }
    
    // Show unknowns
    if (unknowns.length > 0) {
      console.log('\n❓ UNKNOWN (Not in false positive dataset):');
      console.log('-' .repeat(60));
      
      unknowns.forEach((unknown, index) => {
        console.log(`${index + 1}. ${unknown.image_id} (${unknown.baseFilename})`);
        console.log(`   Reason: ${unknown.review_reason || 'Not specified'}`);
      });
    }
    
    // Step 5: Create detailed report for expert
    console.log('\n5️⃣ Creating expert review report...');
    
    const reportData = {
      analysis_focus: "Barry's 'flag for review' classifications vs false positive data",
      summary: {
        total_barry_review_classifications: barryReviewClassifications.length,
        agreements: agreements.length,
        discrepancies: discrepancies.length,
        unknowns: unknowns.length,
        generated_at: new Date().toISOString()
      },
      discrepancies: discrepancies,
      agreements: agreements,
      unknowns: unknowns,
      critical_actions: [
        'Manually inspect each discrepancy image listed above',
        'Determine if flags in discrepancy images are genuinely visible and classifiable',
        'Compare Barry\'s visual assessment with original false positive expert analysis',
        'Update false positive data if Barry\'s assessments are correct',
        'Provide training/feedback if false positive data is correct',
        'Document all decisions for quality control tracking'
      ],
      expert_questions: [
        'Are the flags in discrepancy images clearly visible to human experts?',
        'Do the flags meet the classification criteria used in the original analysis?',
        'Are there image quality issues that might affect flag visibility?',
        'Should the classification guidelines be clarified based on these cases?'
      ]
    };
    
    // Save detailed report
    const reportPath = 'scripts/barry-review-discrepancies-report.json';
    fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2));
    
    console.log(`   ✅ Detailed report saved to: ${reportPath}`);
    
    // Step 6: Final assessment
    console.log('\n6️⃣ QUALITY CONTROL ASSESSMENT');
    console.log('=' .repeat(50));
    
    if (discrepancies.length === 0) {
      console.log('🟢 EXCELLENT: No discrepancies found');
      console.log('   Barry\'s review flags align with false positive analysis');
      console.log('   High confidence in both expert assessments');
    } else {
      const discrepancyRate = (discrepancies.length / barryReviewClassifications.length) * 100;
      console.log(`📊 Discrepancy rate: ${discrepancyRate.toFixed(1)}% (${discrepancies.length}/${barryReviewClassifications.length})`);
      
      if (discrepancyRate <= 10) {
        console.log('🟡 MINOR ISSUES: Low discrepancy rate, spot checks recommended');
      } else if (discrepancyRate <= 25) {
        console.log('🟠 MODERATE ISSUES: Review needed, possible guidance clarification required');
      } else {
        console.log('🔴 MAJOR ISSUES: High discrepancy rate, systematic review required');
      }
      
      console.log('\n📋 NEXT STEPS:');
      console.log(`   1. Review ${discrepancies.length} discrepancy images manually`);
      console.log('   2. Meet with both Barry and original false positive expert');
      console.log('   3. Clarify classification criteria if needed');
      console.log('   4. Update false positive data or provide expert feedback');
      console.log('   5. Re-run this analysis after corrections');
    }
    
  } catch (error) {
    console.error('❌ Error during analysis:', error);
  }
}

// Run the focused analysis
checkBarryReviewVsFalsePositives().catch(console.error); 