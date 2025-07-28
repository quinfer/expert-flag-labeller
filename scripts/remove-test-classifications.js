// scripts/remove-test-classifications.js
import { supabaseAdmin } from '../lib/supabase-admin.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function removeTestClassifications() {
  console.log('🧹 Removing test classifications from before June 2025...\n');
  
  try {
    // First, let's see what we're about to remove
    const { data: testClassifications, error: fetchError } = await supabaseAdmin
      .from('classifications')
      .select('*')
      .lt('timestamp', '2025-06-01T00:00:00.000Z')
      .order('timestamp', { ascending: true });
      
    if (fetchError) {
      console.error('Error fetching test classifications:', fetchError);
      return;
    }
    
    if (!testClassifications || testClassifications.length === 0) {
      console.log('No test classifications found before June 2025.');
      return;
    }
    
    console.log(`📊 Found ${testClassifications.length} test classifications to remove:\n`);
    
    // Group by expert for review
    const byExpert = {};
    testClassifications.forEach(classification => {
      const expert = classification.expert_id || 'unknown';
      if (!byExpert[expert]) {
        byExpert[expert] = [];
      }
      byExpert[expert].push(classification);
    });
    
    // Show what will be removed
    console.log('📋 CLASSIFICATIONS TO BE REMOVED:');
    console.log('='.repeat(60));
    Object.entries(byExpert).forEach(([expert, classifications]) => {
      console.log(`\n👤 ${expert}: ${classifications.length} classifications`);
      const dateRange = classifications.length > 0 ? 
        `${new Date(classifications[0].timestamp).toLocaleDateString()} - ${new Date(classifications[classifications.length - 1].timestamp).toLocaleDateString()}` : 
        'No dates';
      console.log(`   📅 Date range: ${dateRange}`);
      
      // Show towns affected
      const towns = [...new Set(classifications.map(c => c.town).filter(t => t))];
      console.log(`   🏘️  Towns: ${towns.join(', ')}`);
    });
    
    console.log('\n' + '='.repeat(60));
    
    // Ask for confirmation (in real usage, this would be interactive)
    console.log(`\n⚠️  About to remove ${testClassifications.length} test classifications`);
    console.log('This will keep only classifications from June 2025 onwards.');
    
    // Actually remove the test classifications
    const { error: deleteError } = await supabaseAdmin
      .from('classifications')
      .delete()
      .lt('timestamp', '2025-06-01T00:00:00.000Z');
    
    if (deleteError) {
      console.error('❌ Error removing test classifications:', deleteError);
      return;
    }
    
    console.log(`✅ Successfully removed ${testClassifications.length} test classifications`);
    
    // Show what remains
    const { data: remainingClassifications, error: remainingError } = await supabaseAdmin
      .from('classifications')
      .select('expert_id, town, timestamp')
      .order('timestamp', { ascending: true });
      
    if (remainingError) {
      console.error('Error fetching remaining classifications:', remainingError);
      return;
    }
    
    if (remainingClassifications && remainingClassifications.length > 0) {
      console.log(`\n📊 Remaining classifications: ${remainingClassifications.length}`);
      
      const remainingByExpert = {};
      remainingClassifications.forEach(classification => {
        const expert = classification.expert_id || 'unknown';
        if (!remainingByExpert[expert]) {
          remainingByExpert[expert] = [];
        }
        remainingByExpert[expert].push(classification);
      });
      
      console.log('\n📋 REMAINING PRODUCTION CLASSIFICATIONS:');
      console.log('='.repeat(60));
      Object.entries(remainingByExpert).forEach(([expert, classifications]) => {
        console.log(`\n👤 ${expert}: ${classifications.length} classifications`);
        const dateRange = classifications.length > 0 ? 
          `${new Date(classifications[0].timestamp).toLocaleDateString()} - ${new Date(classifications[classifications.length - 1].timestamp).toLocaleDateString()}` : 
          'No dates';
        console.log(`   📅 Date range: ${dateRange}`);
        
        // Show towns affected
        const towns = [...new Set(classifications.map(c => c.town).filter(t => t))];
        console.log(`   🏘️  Towns: ${towns.join(', ')}`);
      });
    } else {
      console.log('\n📊 No remaining classifications (all were test data)');
    }
    
  } catch (error) {
    console.error('❌ Error during cleanup:', error);
  }
}

// Run the cleanup
removeTestClassifications()
  .then(() => {
    console.log('\n✅ Test classification cleanup completed');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Test classification cleanup failed:', error);
    process.exit(1);
  }); 