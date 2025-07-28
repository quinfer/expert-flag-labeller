#!/usr/bin/env node
/**
 * Test script for comprehensive false positive filtering system
 * Tests the system before and after processing all towns
 */

const fs = require('fs');
const path = require('path');

function logSection(title) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`🧪 ${title}`);
  console.log(`${'='.repeat(60)}`);
}

function testCurrentSystem() {
  logSection('TESTING CURRENT SYSTEM');
  
  try {
    // Test existing ENNISKILLEN-only filter
    const enniskillenFilter = JSON.parse(fs.readFileSync('src/data/false-positives-lookup.json', 'utf8'));
    
    console.log('✅ Current ENNISKILLEN filter loaded successfully');
    console.log(`   📊 False positives: ${enniskillenFilter.count}`);
    console.log(`   🏘️  Towns: ${enniskillenFilter.metadata?.total_towns || 1}`);
    console.log(`   📈 FP Rate: ${enniskillenFilter.metadata?.overall_fp_rate?.toFixed(1) || 'N/A'}%`);
    
    return {
      exists: true,
      falsePositives: enniskillenFilter.count,
      towns: enniskillenFilter.metadata?.total_towns || 1,
      fpRate: enniskillenFilter.metadata?.overall_fp_rate || 0
    };
  } catch (error) {
    console.log('❌ Current system not found or invalid');
    return { exists: false };
  }
}

function testTownDataAvailability() {
  logSection('TESTING TOWN DATA AVAILABILITY');
  
  const falsePositiveChecks = 'false_positive_checks';
  
  if (!fs.existsSync(falsePositiveChecks)) {
    console.log('❌ false_positive_checks directory not found');
    return { available: false };
  }
  
  // Find all available towns
  const files = fs.readdirSync(falsePositiveChecks);
  const towns = new Set();
  
  files.forEach(file => {
    if (file.endsWith('list.pickle')) {
      const townName = file.replace('list.pickle', '');
      
      // Check if this town has all required files
      const hasResults = files.includes(`${townName}results.pickle`);
      const hasCorrect = files.includes(`${townName}resultsCORRECT.pickle`);
      
      if (hasResults && hasCorrect) {
        towns.add(townName);
      }
    }
  });
  
  console.log(`✅ Found ${towns.size} towns with complete data sets:`);
  
  const townList = Array.from(towns).sort();
  townList.forEach((town, i) => {
    console.log(`   ${String(i + 1).padStart(2, ' ')}. ${town}`);
  });
  
  return {
    available: true,
    towns: townList,
    totalTowns: towns.size
  };
}

function testProcessingCapability() {
  logSection('TESTING PROCESSING CAPABILITY');
  
  // Check if Python is available
  try {
    const { execSync } = require('child_process');
    const pythonVersion = execSync('python3 --version', { encoding: 'utf8' }).trim();
    console.log(`✅ Python available: ${pythonVersion}`);
    
    // Check required Python packages
    try {
      execSync('python3 -c "import pandas, pickle, numpy"', { encoding: 'utf8' });
      console.log('✅ Required Python packages available (pandas, pickle, numpy)');
      
      return { ready: true };
    } catch (error) {
      console.log('❌ Missing required Python packages');
      console.log('   Run: pip install pandas numpy');
      return { ready: false, reason: 'missing-packages' };
    }
  } catch (error) {
    console.log('❌ Python3 not available');
    return { ready: false, reason: 'no-python' };
  }
}

function testProcessingScript() {
  logSection('TESTING PROCESSING SCRIPT');
  
  const scriptPath = 'scripts/process-all-towns-false-positives.py';
  
  if (!fs.existsSync(scriptPath)) {
    console.log('❌ Processing script not found');
    return { exists: false };
  }
  
  console.log('✅ Processing script found');
  
  // Check if the script looks valid
  const scriptContent = fs.readFileSync(scriptPath, 'utf8');
  const hasMainFunction = scriptContent.includes('def main()');
  const hasGetAvailableTowns = scriptContent.includes('def get_available_towns()');
  const hasProcessSingleTown = scriptContent.includes('def process_single_town(');
  
  if (hasMainFunction && hasGetAvailableTowns && hasProcessSingleTown) {
    console.log('✅ Processing script appears to be complete');
    return { exists: true, valid: true };
  } else {
    console.log('❌ Processing script appears to be incomplete');
    return { exists: true, valid: false };
  }
}

function testOutputDirectories() {
  logSection('TESTING OUTPUT DIRECTORIES');
  
  const srcDataDir = 'src/data';
  const townsDir = 'src/data/towns';
  
  if (!fs.existsSync(srcDataDir)) {
    console.log('❌ src/data directory not found');
    return { ready: false };
  }
  
  console.log('✅ src/data directory exists');
  
  if (!fs.existsSync(townsDir)) {
    console.log('📁 Creating towns directory...');
    fs.mkdirSync(townsDir, { recursive: true });
    console.log('✅ Towns directory created');
  } else {
    console.log('✅ Towns directory already exists');
  }
  
  return { ready: true };
}

function simulateProcessing() {
  logSection('SIMULATING PROCESSING');
  
  // Simulate what the comprehensive filter would look like
  const sampleTowns = ['ANTRIM', 'ARMAGH', 'BANGOR', 'BELFAST CITY', 'ENNISKILLEN'];
  const simulatedStats = {
    totalTowns: 50,
    estimatedFalsePositives: 500000, // Rough estimate based on ENNISKILLEN
    estimatedTruePositives: 15000,
    overallFpRate: 97.1
  };
  
  console.log('📊 Estimated comprehensive filter statistics:');
  console.log(`   🏘️  Total towns: ${simulatedStats.totalTowns}`);
  console.log(`   ❌ Est. false positives: ${simulatedStats.estimatedFalsePositives.toLocaleString()}`);
  console.log(`   ✅ Est. true positives: ${simulatedStats.estimatedTruePositives.toLocaleString()}`);
  console.log(`   📈 Est. FP rate: ${simulatedStats.overallFpRate}%`);
  
  return simulatedStats;
}

function testFilteringIntegration() {
  logSection('TESTING FILTERING INTEGRATION');
  
  // Test if the false positive filter can be imported
  try {
    const filterPath = 'src/lib/false-positive-filter.ts';
    
    if (!fs.existsSync(filterPath)) {
      console.log('❌ False positive filter not found');
      return { integrated: false };
    }
    
    const filterContent = fs.readFileSync(filterPath, 'utf8');
    
    // Check for comprehensive filtering features
    const hasComprehensiveInterface = filterContent.includes('total_towns');
    const hasDetailedStats = filterContent.includes('getDetailedStats');
    const hasMetadata = filterContent.includes('metadata');
    
    if (hasComprehensiveInterface && hasDetailedStats && hasMetadata) {
      console.log('✅ Filter has comprehensive features');
      console.log('   ✅ Multi-town support');
      console.log('   ✅ Detailed statistics');
      console.log('   ✅ Metadata support');
      
      return { integrated: true, features: 'comprehensive' };
    } else {
      console.log('⚠️  Filter exists but may need updates for comprehensive data');
      return { integrated: true, features: 'basic' };
    }
  } catch (error) {
    console.log('❌ Error checking filter integration');
    return { integrated: false };
  }
}

function generateProcessingPlan() {
  logSection('PROCESSING PLAN');
  
  console.log('📋 Recommended processing steps:');
  console.log('   1. ✅ Run processing script: python3 scripts/process-all-towns-false-positives.py');
  console.log('   2. ✅ Verify town data files created in src/data/towns/');
  console.log('   3. ✅ Check comprehensive filter: src/data/false-positives-comprehensive.json');
  console.log('   4. ✅ Update app to use new lookup: src/data/false-positives-lookup-all.json');
  console.log('   5. ✅ Test API endpoints for improved filtering');
  console.log('   6. ✅ Monitor filter performance and statistics');
  
  console.log('\n📊 Expected improvements:');
  console.log('   📈 False positive filtering across all 50 towns');
  console.log('   📈 Comprehensive statistics and metadata');
  console.log('   📈 Better API response information');
  console.log('   📈 Scalable system for additional towns');
}

function main() {
  console.log('🧪 COMPREHENSIVE FALSE POSITIVE FILTER TEST');
  console.log('='*60);
  
  const tests = {
    currentSystem: testCurrentSystem(),
    townData: testTownDataAvailability(),
    processing: testProcessingCapability(),
    script: testProcessingScript(),
    output: testOutputDirectories(),
    integration: testFilteringIntegration()
  };
  
  // Simulation and planning
  const simulation = simulateProcessing();
  
  // Generate processing plan
  generateProcessingPlan();
  
  // Summary
  logSection('SUMMARY');
  
  const readiness = {
    dataAvailable: tests.townData.available,
    processingReady: tests.processing.ready,
    scriptReady: tests.script.exists && tests.script.valid,
    outputReady: tests.output.ready,
    integrationReady: tests.integration.integrated
  };
  
  const overallReady = Object.values(readiness).every(ready => ready);
  
  console.log(`📊 System readiness: ${overallReady ? '✅ READY' : '⚠️  NEEDS ATTENTION'}`);
  console.log(`   📁 Data available: ${readiness.dataAvailable ? '✅' : '❌'}`);
  console.log(`   🐍 Processing ready: ${readiness.processingReady ? '✅' : '❌'}`);
  console.log(`   📝 Script ready: ${readiness.scriptReady ? '✅' : '❌'}`);
  console.log(`   📂 Output ready: ${readiness.outputReady ? '✅' : '❌'}`);
  console.log(`   🔗 Integration ready: ${readiness.integrationReady ? '✅' : '❌'}`);
  
  if (overallReady) {
    console.log('\n🎉 System is ready for comprehensive false positive processing!');
    console.log('   Run: python3 scripts/process-all-towns-false-positives.py');
  } else {
    console.log('\n⚠️  Please address the issues above before proceeding.');
  }
  
  return { ready: overallReady, tests, simulation };
}

if (require.main === module) {
  main();
}

module.exports = { main }; 