import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get current directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Sample image to test
const sampleImagePath = path.join(projectRoot, 'public', 'images', 'ANTRIM', '22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg');

console.log("Testing image access...");
console.log("Project root path:", projectRoot);
console.log("Sample image full path:", sampleImagePath);
console.log("File exists?", fs.existsSync(sampleImagePath));

// Check directory structure
const publicDir = path.join(projectRoot, 'public');
const imagesDir = path.join(publicDir, 'images');
const antrimDir = path.join(imagesDir, 'ANTRIM');

console.log("\nChecking directory structure:");
console.log("- public dir exists?", fs.existsSync(publicDir));
console.log("- images dir exists?", fs.existsSync(imagesDir));
console.log("- ANTRIM dir exists?", fs.existsSync(antrimDir));

// List files in ANTRIM dir
if (fs.existsSync(antrimDir)) {
  console.log("\nFirst 5 files in ANTRIM directory:");
  const files = fs.readdirSync(antrimDir).slice(0, 5);
  files.forEach(file => {
    const filePath = path.join(antrimDir, file);
    const stats = fs.statSync(filePath);
    console.log(`- ${file} (${stats.size} bytes)`);
  });
}

// Test relative path that would be used in browser
const relativePath = '/images/ANTRIM/22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg';
console.log("\nRelative path that would be used in browser:", relativePath);

// Test all possible path variations that might be used
const pathVariations = [
  '/images/ANTRIM/22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg',
  'images/ANTRIM/22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg',
  '/public/images/ANTRIM/22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg',
  'public/images/ANTRIM/22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg',
];

console.log("\nTesting all possible path variations:");
pathVariations.forEach(testPath => {
  const fullPath = path.join(projectRoot, testPath.replace(/^\//, ''));
  console.log(`- ${testPath}: ${fs.existsSync(fullPath) ? 'EXISTS' : 'NOT FOUND'}`);
});

// Special check for Next.js public directory convention
console.log("\nSpecial check for Next.js public paths:");
const nextPublicPath = path.join(projectRoot, 'public', relativePath.replace(/^\//, ''));
console.log(`- Next.js public path: ${nextPublicPath}`);
console.log(`- Exists? ${fs.existsSync(nextPublicPath)}`);