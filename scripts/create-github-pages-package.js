import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function createGitHubPagesPackage() {
  console.log('🚀 CREATING GITHUB PAGES PACKAGE');
  console.log('=' .repeat(50));
  
  // Create output directory
  const outputDir = path.join(__dirname, '..', 'github-pages-report');
  const imagesDir = path.join(outputDir, 'images');
  
  // Clean and create directories
  if (fs.existsSync(outputDir)) {
    fs.rmSync(outputDir, { recursive: true });
  }
  fs.mkdirSync(outputDir, { recursive: true });
  fs.mkdirSync(imagesDir, { recursive: true });
  
  console.log('1️⃣ Setting up directory structure...');
  console.log(`   Output: ${outputDir}`);
  
  // List of disputed images from the barry-review-discrepancies-report.json
  const disputedImages = [
    'ZP55Ydb9H8Y1cEWYhYAgzw_240',
    'TJG87O8jBgd8dzwiuPR1KQ_060', 
    'NREaXVjDT4hgBgfT92v0Iw_180',
    'GP27ckTW5bwq6AOmCMnCAg_000',
    'uxN0xRE9t4To6LBtKkw2og_120',
    'Xdkhj2ivRF_-3zcuwy9DNg_120',
    'nuyOVyoGQSFo_l3h1_LEtg_060',
    'pGAolNdN7sLGI3ZWGyi8Ug_300',
    'hHaZXLSlTRgbAtC5sN5BmQ_120',
    'Kl0NZDrCatcCSiQ33GmT-A_240',
    'tPVDI_bSrwOEzO7l2phMqg_240',
    'rQT_klvRS88UOGC22DDHmQ_000',
    'Qi23_GKOLB7-MAIlXqDSEg_120',
    'v8wy7PM7Jqqog4R_HtbbQQ_240',
    'ScH0zbysQKCbisaBWfC9uw_180',
    'XGRAUZTmsPD6VHCK3Ksk-Q_300',
    'ECjMwwOBqPh8Gs1rg0x8jA_180',
    'mRv77-0EbxsE5O8MW_SEvA_000',
    'r8OFBKqHRBGR-LVrfy6FIA_180'
  ];
  
  console.log('2️⃣ Copying required images...');
  
  const sourceImageDir = path.join(__dirname, '..', 'public', 'images', 'ENNISKILLEN');
  let copiedCount = 0;
  
  for (const baseImage of disputedImages) {
    // Copy original panoramic image
    const originalFile = `${baseImage}.jpg`;
    const originalSrc = path.join(sourceImageDir, originalFile);
    const originalDest = path.join(imagesDir, originalFile);
    
    if (fs.existsSync(originalSrc)) {
      fs.copyFileSync(originalSrc, originalDest);
      copiedCount++;
      console.log(`   ✅ ${originalFile}`);
    } else {
      console.log(`   ❌ Missing: ${originalFile}`);
    }
    
    // Copy cropped versions - check for all possible box indices
    for (let boxIndex = 0; boxIndex <= 10; boxIndex++) {
      const croppedFile = `${baseImage}_box${boxIndex}.jpg`;
      const croppedSrc = path.join(sourceImageDir, croppedFile);
      const croppedDest = path.join(imagesDir, croppedFile);
      
      if (fs.existsSync(croppedSrc)) {
        fs.copyFileSync(croppedSrc, croppedDest);
        copiedCount++;
        console.log(`   ✅ ${croppedFile}`);
      }
    }
  }
  
  console.log(`   Total images copied: ${copiedCount}`);
  
  console.log('3️⃣ Creating GitHub Pages HTML...');
  
  // Read the current report and modify paths
  const reportPath = path.join(__dirname, 'visual-discrepancy-report.html');
  let htmlContent = fs.readFileSync(reportPath, 'utf8');
  
  // Replace image paths for GitHub Pages
  htmlContent = htmlContent.replace(
    /\.\.\/public\/images\/ENNISKILLEN\//g, 
    './images/'
  );
  
  // Update title and add GitHub Pages specific content
  htmlContent = htmlContent.replace(
    '<title>Expert Review: Disputed Image Classifications</title>',
    '<title>Expert Flag Classification Review - ENNISKILLEN Disputed Cases</title>'
  );
  
  // Add GitHub repository info in header
  htmlContent = htmlContent.replace(
    '<p><strong>Generated:</strong>',
    '<p><strong>🔗 GitHub Repository:</strong> <a href="https://github.com/yourusername/expert-flag-discrepancy-report" target="_blank">View Source</a></p>\n        <p><strong>📊 Dataset:</strong> ENNISKILLEN False Positive Analysis</p>\n        <p><strong>Generated:</strong>'
  );
  
  // Write the modified HTML
  const indexPath = path.join(outputDir, 'index.html');
  fs.writeFileSync(indexPath, htmlContent);
  
  console.log('4️⃣ Creating README.md...');
  
  const readmeContent = `# Expert Flag Classification Review
## ENNISKILLEN Disputed Cases Analysis

### 🎯 Purpose
This interactive report presents 19 disputed flag classifications from ENNISKILLEN where expert Barry's field assessments conflict with existing false positive data classifications.

### 📊 The Conflict
- **Barry's Assessment**: These 19 images should NOT be shown to experts (false positives)
- **Dataset Classification**: These same 19 images are marked as TRUE POSITIVES containing genuine flags
- **Disagreement Rate**: 100% - Complete conflict requiring expert review

### 🔍 Review Process
1. **Visual Inspection**: Each disputed image is shown with both original panoramic view and cropped flag region
2. **Expert Decision**: Reviewers determine who is correct using the interactive buttons
3. **Data Export**: Decisions can be exported as JSON for system updates

### 📈 Dataset Context
- **Total Images Processed**: 33,864
- **CV-Positive Images**: 1,289 (sent for expert review)
- **True Positives**: 793 (expert confirmed flags)
- **False Positives**: 496 (expert rejected flags)
- **Positive Predictive Value**: 61.5%

### 🚨 Critical Finding
All 19 disputed images are classified as true positives in the dataset but Barry flagged them as false positives, indicating potential systematic error requiring immediate expert attention.

### 🔧 Technical Details
- **Interactive HTML Report**: Side-by-side image comparison
- **Auto-save Progress**: Uses browser localStorage
- **Export Functionality**: JSON export of decisions
- **Responsive Design**: Works on desktop and mobile

### 📝 Usage
1. Open \`index.html\` in your browser
2. Review each disputed image carefully
3. Make decisions using the provided buttons
4. Export your decisions when complete

### 🎨 Image Types
Each disputed case shows:
- **Original Panoramic**: Full street view context
- **Cropped Region**: Specific flag area that Barry classified

Generated: ${new Date().toISOString()}
`;

  fs.writeFileSync(path.join(outputDir, 'README.md'), readmeContent);
  
  console.log('5️⃣ Creating deployment instructions...');
  
  const deployContent = `# GitHub Pages Deployment Instructions

## Quick Setup

### Option 1: New Repository (Recommended)
1. Create new GitHub repository: \`expert-flag-discrepancy-report\`
2. Upload all files from this directory to the repository
3. Go to Settings > Pages > Source: Deploy from a branch > main
4. Your report will be available at: \`https://yourusername.github.io/expert-flag-discrepancy-report/\`

### Option 2: Existing Repository
1. Create \`docs/\` folder in your existing repository
2. Copy all files to \`docs/\` folder
3. Go to Settings > Pages > Source: Deploy from a branch > main > /docs
4. Your report will be available at: \`https://yourusername.github.io/your-repo-name/\`

## File Structure
\`\`\`
expert-flag-discrepancy-report/
├── index.html                     # Main report (${Math.round(fs.statSync(indexPath).size / 1024)}KB)
├── images/                        # ${copiedCount} disputed images (~${Math.round(copiedCount * 150 / 1024)}MB total)
│   ├── ZP55Ydb9H8Y1cEWYhYAgzw_240.jpg
│   ├── ZP55Ydb9H8Y1cEWYhYAgzw_240_box0.jpg
│   └── [additional images...]
├── README.md                      # Documentation
└── DEPLOY.md                      # This file
\`\`\`

## Sharing
Once deployed, share this URL with colleagues for expert review:
\`https://yourusername.github.io/expert-flag-discrepancy-report/\`

The report is fully interactive and includes:
- ✅ Side-by-side image comparison
- ✅ Interactive decision buttons
- ✅ Progress tracking
- ✅ Auto-save functionality
- ✅ JSON export of decisions
- ✅ Professional presentation
`;

  fs.writeFileSync(path.join(outputDir, 'DEPLOY.md'), deployContent);
  
  console.log('6️⃣ Creating .gitignore...');
  fs.writeFileSync(path.join(outputDir, '.gitignore'), `# Editor files
.DS_Store
Thumbs.db
*.swp
*.swo

# Temporary files
*.tmp
*.temp
`);
  
  console.log('✅ GITHUB PAGES PACKAGE COMPLETE!');
  console.log('=' .repeat(50));
  console.log(`📁 Package location: ${outputDir}`);
  console.log(`📊 Images copied: ${copiedCount}`);
  console.log(`📄 Files created: index.html, README.md, DEPLOY.md, .gitignore`);
  console.log();
  console.log('🚀 NEXT STEPS:');
  console.log('1. Create new GitHub repository: expert-flag-discrepancy-report');
  console.log('2. Upload all files from the package directory');
  console.log('3. Enable GitHub Pages in repository settings');
  console.log('4. Share the resulting URL with colleagues');
  console.log();
  console.log('💡 The report will be accessible at:');
  console.log('   https://yourusername.github.io/expert-flag-discrepancy-report/');
}

createGitHubPagesPackage().catch(console.error); 