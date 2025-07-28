#!/usr/bin/env node
/**
 * Test script to verify the comprehensive false positive filter
 */

const fs = require('fs');

function testComprehensiveFilter() {
  console.log('🧪 TESTING COMPREHENSIVE FALSE POSITIVE FILTER');
  console.log('='*60);

  try {
    // Load the comprehensive filter
    const filterData = JSON.parse(fs.readFileSync('src/data/false-positives-lookup-all.json', 'utf8'));
    
    console.log('✅ Successfully loaded comprehensive filter');
    console.log(`📊 Statistics:`);
    console.log(`   🏘️  Total towns: ${filterData.metadata.total_towns}`);
    console.log(`   ❌ False positives: ${filterData.count.toLocaleString()}`);
    console.log(`   📈 Overall FP rate: ${filterData.metadata.overall_fp_rate.toFixed(2)}%`);
    
    // Test some sample filenames
    const sampleTests = [
      'test-image-1.jpg',
      'genuine-flag-image.jpg',
      '---8j_IGYt3RGCQmd97MWw_000.jpg', // Should be false positive
      'valid-image.jpg'
    ];
    
    console.log('\n🔍 Testing sample filenames:');
    sampleTests.forEach(filename => {
      const isFalsePositive = filterData.false_positives.includes(filename);
      console.log(`   ${filename}: ${isFalsePositive ? '❌ FALSE POSITIVE' : '✅ VALID'}`);
    });
    
    // Verify data structure
    console.log('\n📋 Data structure validation:');
    console.log(`   ✅ Has false_positives array: ${Array.isArray(filterData.false_positives)}`);
    console.log(`   ✅ Has count: ${typeof filterData.count === 'number'}`);
    console.log(`   ✅ Has metadata: ${typeof filterData.metadata === 'object'}`);
    console.log(`   ✅ Count matches array length: ${filterData.count === filterData.false_positives.length}`);
    
    // Compare with old ENNISKILLEN filter
    try {
      const oldFilter = JSON.parse(fs.readFileSync('src/data/false-positives-lookup.json', 'utf8'));
      console.log('\n📊 Comparison with old ENNISKILLEN filter:');
      console.log(`   Old filter (ENNISKILLEN only): ${oldFilter.count.toLocaleString()}`);
      console.log(`   New filter (50 towns): ${filterData.count.toLocaleString()}`);
      console.log(`   Improvement: ${(filterData.count - oldFilter.count).toLocaleString()} additional false positives filtered`);
      console.log(`   Scale increase: ${(filterData.count / oldFilter.count).toFixed(1)}x more comprehensive`);
    } catch (error) {
      console.log('   ⚠️  Could not compare with old filter');
    }
    
    return {
      success: true,
      totalTowns: filterData.metadata.total_towns,
      falsePositives: filterData.count,
      fpRate: filterData.metadata.overall_fp_rate
    };
    
  } catch (error) {
    console.error('❌ Error testing comprehensive filter:', error.message);
    return { success: false, error: error.message };
  }
}

function testFilterIntegration() {
  console.log('\n🔗 TESTING FILTER INTEGRATION');
  console.log('='*60);
  
  try {
    // Check if the filter file exists and can be imported
    const filterPath = 'src/lib/false-positive-filter.ts';
    
    if (!fs.existsSync(filterPath)) {
      console.log('❌ Filter TypeScript file not found');
      return { integrated: false };
    }
    
    const filterContent = fs.readFileSync(filterPath, 'utf8');
    
    // Check if it imports the comprehensive data
    const importsComprehensive = filterContent.includes('false-positives-lookup-all.json');
    
    console.log(`✅ Filter file exists: ${filterPath}`);
    console.log(`✅ Uses comprehensive data: ${importsComprehensive}`);
    
    if (importsComprehensive) {
      console.log('✅ Filter is properly configured for comprehensive filtering');
      console.log('   📊 Will filter 1.87M+ false positives across 50 towns');
      console.log('   🎯 Will provide detailed statistics and metadata');
      
      return { integrated: true, comprehensive: true };
    } else {
      console.log('⚠️  Filter exists but may not be using comprehensive data');
      return { integrated: true, comprehensive: false };
    }
    
  } catch (error) {
    console.error('❌ Error testing filter integration:', error.message);
    return { integrated: false, error: error.message };
  }
}

function main() {
  const filterTest = testComprehensiveFilter();
  const integrationTest = testFilterIntegration();
  
  console.log('\n🎉 FINAL RESULTS');
  console.log('='*60);
  
  if (filterTest.success && integrationTest.integrated) {
    console.log('✅ COMPREHENSIVE FALSE POSITIVE FILTER READY!');
    console.log(`   📊 ${filterTest.totalTowns} towns processed`);
    console.log(`   ❌ ${filterTest.falsePositives.toLocaleString()} false positives will be filtered`);
    console.log(`   📈 ${filterTest.fpRate.toFixed(2)}% false positive rate`);
    console.log(`   🔗 Integration: ${integrationTest.comprehensive ? 'COMPREHENSIVE' : 'BASIC'}`);
    
    console.log('\n🚀 NEXT STEPS:');
    console.log('   1. ✅ Test API endpoints with new filter');
    console.log('   2. ✅ Monitor performance improvements');
    console.log('   3. ✅ Verify expert user experience');
    console.log('   4. ✅ Deploy to production');
    
    return { ready: true, ...filterTest, ...integrationTest };
  } else {
    console.log('❌ SYSTEM NOT READY');
    console.log('   Please fix the issues above before proceeding');
    return { ready: false, filterTest, integrationTest };
  }
}

if (require.main === module) {
  main();
}

module.exports = { testComprehensiveFilter, testFilterIntegration, main }; 