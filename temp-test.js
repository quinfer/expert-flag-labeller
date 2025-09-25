console.log('Testing false positive lookup data...');
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('src/data/false-positives-lookup.json', 'utf8'));
console.log('✅ False positive entries loaded:', data.count);
console.log('✅ Sample false positives:');
data.false_positives.slice(0, 5).forEach((fp, i) => console.log('  ', i+1, fp));
console.log('✅ System ready for false positive filtering!');
