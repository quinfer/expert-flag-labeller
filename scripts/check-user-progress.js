// scripts/check-user-progress.js
import { supabaseAdmin } from '../lib/supabase-admin.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function checkUserProgress() {
  console.log('🔍 Checking user progress across towns...\n');
  
  try {
    // Get all classifications with expert_id and town
    const { data: classifications, error } = await supabaseAdmin
      .from('classifications')
      .select('expert_id, town, image_id, timestamp')
      .order('timestamp', { ascending: true });
      
    if (error) {
      console.error('Error fetching classifications:', error);
      return;
    }
    
    if (!classifications || classifications.length === 0) {
      console.log('No classifications found.');
      return;
    }
    
    console.log(`📊 Found ${classifications.length} total classifications\n`);
    
    // Group by expert_id
    const userProgress = {};
    
    classifications.forEach(classification => {
      const { expert_id, town, image_id, timestamp } = classification;
      
      if (!userProgress[expert_id]) {
        userProgress[expert_id] = {
          towns: new Set(),
          totalClassifications: 0,
          firstClassification: timestamp,
          lastClassification: timestamp,
          townDetails: {}
        };
      }
      
      const userStats = userProgress[expert_id];
      userStats.towns.add(town || 'UNKNOWN');
      userStats.totalClassifications++;
      
      if (timestamp < userStats.firstClassification) {
        userStats.firstClassification = timestamp;
      }
      if (timestamp > userStats.lastClassification) {
        userStats.lastClassification = timestamp;
      }
      
      // Track count per town
      const townName = town || 'UNKNOWN';
      if (!userStats.townDetails[townName]) {
        userStats.townDetails[townName] = 0;
      }
      userStats.townDetails[townName]++;
    });
    
    // Display results
    console.log('👥 USER PROGRESS SUMMARY:\n');
    console.log('='.repeat(60));
    
    Object.entries(userProgress).forEach(([expertId, stats]) => {
      const townsArray = Array.from(stats.towns).sort();
      const hasMovedBeyondEnniskillen = townsArray.some(town => 
        town && town.toUpperCase() !== 'ENNISKILLEN'
      );
      
      console.log(`\n👤 Expert: ${expertId}`);
      console.log(`   📈 Total Classifications: ${stats.totalClassifications}`);
      console.log(`   🏘️  Towns Worked On: ${townsArray.length}`);
      console.log(`   📅 First Classification: ${new Date(stats.firstClassification).toLocaleDateString()}`);
      console.log(`   📅 Last Classification: ${new Date(stats.lastClassification).toLocaleDateString()}`);
      
      if (hasMovedBeyondEnniskillen) {
        console.log(`   ✅ Has moved beyond Enniskillen: YES`);
      } else {
        console.log(`   ❌ Has moved beyond Enniskillen: NO`);
      }
      
      console.log(`   🏘️  Town Breakdown:`);
      Object.entries(stats.townDetails).forEach(([town, count]) => {
        console.log(`      - ${town}: ${count} classifications`);
      });
      
      console.log(`   🗺️  Towns: ${townsArray.join(', ')}`);
    });
    
    console.log('\n' + '='.repeat(60));
    
    // Summary stats
    const totalUsers = Object.keys(userProgress).length;
    const usersMovedBeyond = Object.values(userProgress).filter(stats => 
      Array.from(stats.towns).some(town => town && town.toUpperCase() !== 'ENNISKILLEN')
    ).length;
    
    console.log(`\n📋 SUMMARY:`);
    console.log(`   Total active users: ${totalUsers}`);
    console.log(`   Users still on Enniskillen only: ${totalUsers - usersMovedBeyond}`);
    console.log(`   Users moved beyond Enniskillen: ${usersMovedBeyond}`);
    
    if (usersMovedBeyond > 0) {
      console.log(`\n🎉 ${usersMovedBeyond} user(s) have progressed beyond the first batch!`);
    } else {
      console.log(`\n⏳ All users are still working on the first batch (Enniskillen)`);
    }
    
  } catch (error) {
    console.error('Error checking user progress:', error);
  }
}

// Run the check
checkUserProgress()
  .then(() => {
    console.log('\n✅ Progress check completed');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Progress check failed:', error);
    process.exit(1);
  }); 