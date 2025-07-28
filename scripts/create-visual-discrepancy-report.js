import { supabaseAdmin } from '../lib/supabase-admin.js';
import fs from 'fs';
import path from 'path';

// Helper function to extract base filename from composite images
function extractBaseFilename(filename) {
  if (filename.includes('_box') && filename.endsWith('.jpg')) {
    return filename.replace(/_box\d+\.jpg$/, '');
  }
  if (filename.startsWith('composite_')) {
    const withoutComposite = filename.replace('composite_', '');
    return withoutComposite.replace(/_box\d+\.jpg$/, '');
  }
  if (filename.endsWith('.jpg')) {
    return filename.replace('.jpg', '');
  }
  return filename;
}

async function createVisualDiscrepancyReport() {
  console.log('📊 CREATING VISUAL DISCREPANCY REPORT');
  console.log('=' .repeat(50));
  console.log();
  
  try {
    // Step 1: Get Barry's "Review" classifications
    console.log('1️⃣ Loading Barry\'s disputed classifications...');
    const { data: barryReviewClassifications, error: barryError } = await supabaseAdmin
      .from('classifications')
      .select('*')
      .eq('expert_id', 'Barry')
      .eq('town', 'ENNISKILLEN')
      .eq('primary_category', 'Review')
      .order('timestamp', { ascending: true });
      
    if (barryError) {
      console.error('❌ Error fetching Barry\'s classifications:', barryError);
      return;
    }
    
    console.log(`   ✅ Found ${barryReviewClassifications?.length || 0} disputed images`);
    
    if (!barryReviewClassifications || barryReviewClassifications.length === 0) {
      console.log('   ℹ️  No disputed images found.');
      return;
    }
    
    // Step 2: Load false positive data
    console.log('\n2️⃣ Loading false positive data for cross-reference...');
    
    let falsePositiveData;
    try {
      const { execSync } = await import('child_process');
      
      // Get the disputed filenames for filtering
      const disputedBaseFilenames = barryReviewClassifications.map(c => 
        extractBaseFilename(c.image_id)
      );
      
      // Write the disputed filenames to a temporary file to avoid Python syntax issues
      const tempFile = 'scripts/temp_disputed_filenames.json';
      fs.writeFileSync(tempFile, JSON.stringify(disputedBaseFilenames));
      
      const pythonScript = `
import pickle
import pandas as pd
import json

# Load disputed filenames from temp file
with open('scripts/temp_disputed_filenames.json', 'r') as f:
    disputed_filenames = json.load(f)

df = pd.read_pickle('false_positive_checks/ENNISKILLENresultsCORRECT.pickle')
true_positives = set(df[df['indicator'] == '1.0']['f'].tolist())

# Get disputed rows specifically
disputed_rows = df[df['f'].isin(disputed_filenames)]

# Get a sample of the overall data for context
sample_size = min(50, len(df))
sample_df = df.sample(n=sample_size)

# Convert to records for JSON serialization, handling NaN values
disputed_rows_clean = disputed_rows.fillna('null')
sample_df_clean = sample_df.fillna('null')

disputed_records = disputed_rows_clean.to_dict('records')
sample_records = sample_df_clean.to_dict('records')

# Convert numpy int64 to regular int for JSON serialization
def clean_for_json(obj):
    if str(obj) == 'null' or str(obj) == 'nan':
        return None
    if hasattr(obj, 'item'):  # numpy types
        return obj.item()
    return obj

# Clean the records
disputed_records = [{k: clean_for_json(v) for k, v in record.items()} for record in disputed_records]
sample_records = [{k: clean_for_json(v) for k, v in record.items()} for record in sample_records]

result = {
  'true_positives': list(true_positives),
  'disputed_data': disputed_records,
  'sample_data': sample_records,
  'total_records': len(df),
  'columns': list(df.columns),
      'data_summary': {
      'total_images': len(df),
      'cv_positive_images': len(df[df['flags'] != 0]),
      'cv_negative_images': len(df[df['flags'] == 0]),
      'true_positives': len(df[df['indicator'] == '1.0']),
      'false_positives': len(df[(df['flags'] != 0) & (df['flags_correct'] == 0)]),
      'flags_distribution': {str(k): int(v) for k, v in df['flags'].value_counts().to_dict().items()},
      'flags_correct_distribution': {str(k): int(v) for k, v in df['flags_correct'].value_counts().to_dict().items()}
    }
}

print(json.dumps(result))
      `;
      
      const pythonResult = execSync(`python3 -c "${pythonScript}"`, { encoding: 'utf8' });
      falsePositiveData = JSON.parse(pythonResult);
      
      // Clean up temporary file
      if (fs.existsSync(tempFile)) {
        fs.unlinkSync(tempFile);
      }
      
      console.log(`   ✅ Loaded false positive data with ${falsePositiveData.disputed_data.length} disputed records`);
      
    } catch (error) {
      console.error('❌ Error loading false positive data:', error);
      // Clean up temporary file on error too
      const tempFile = 'scripts/temp_disputed_filenames.json';
      if (fs.existsSync(tempFile)) {
        fs.unlinkSync(tempFile);
      }
      return;
    }
    
    // Step 3: Create HTML report
    console.log('\n3️⃣ Generating visual HTML report...');
    
    const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Expert Review: Disputed Image Classifications</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .summary {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .dispute-item {
            background: white;
            border-radius: 8px;
            margin-bottom: 30px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 5px solid #ff6b6b;
        }
        .dispute-header {
            background: #ffebee;
            padding: 15px 20px;
            border-bottom: 1px solid #ffcdd2;
        }
        .dispute-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 20px;
        }
        .assessment-panel {
            padding: 15px;
            border-radius: 6px;
            border: 2px solid #ddd;
        }
        .barry-assessment {
            background: #e8f5e8;
            border-color: #4caf50;
        }
        .data-assessment {
            background: #fff3e0;
            border-color: #ff9800;
        }
        .image-container {
            grid-column: span 2;
            text-align: center;
            margin-top: 20px;
            padding: 20px;
            background: #fafafa;
            border-radius: 6px;
        }
        .dispute-image {
            max-width: 100%;
            max-height: 400px;
            border: 3px solid #ff6b6b;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .decision-area {
            grid-column: span 2;
            margin-top: 20px;
            padding: 20px;
            background: #f0f7ff;
            border: 2px dashed #2196f3;
            border-radius: 6px;
        }
        .decision-buttons {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn-barry { background: #4caf50; color: white; }
        .btn-data { background: #ff9800; color: white; }
        .btn-unclear { background: #9e9e9e; color: white; }
        .metadata {
            font-size: 0.9em;
            color: #666;
            margin-top: 10px;
        }
        .conflict-badge {
            display: inline-block;
            background: #ff5722;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .instructions {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 5px solid #2196f3;
        }
        .navigation {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .progress {
            background: #ddd;
            height: 8px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .progress-bar {
            background: #4caf50;
            height: 100%;
            border-radius: 4px;
            width: 0%;
            transition: width 0.3s;
        }
        @media print {
            .navigation { display: none; }
            .dispute-item { break-inside: avoid; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Expert Review: Disputed Image Classifications</h1>
        <p>Reconciliation between Barry's assessments and false positive data</p>
        <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
    </div>

    <div class="instructions">
        <h3>📋 Review Instructions</h3>
        <p><strong>Purpose:</strong> Barry flagged these ${barryReviewClassifications.length} images as "false positives" or "unclear", but the false positive data indicates they contain genuine flags.</p>
        <p><strong>Your task:</strong> For each image below, determine who is correct:</p>
        <ul>
            <li><strong>Barry's Assessment:</strong> Image doesn't contain a classifiable flag (or is unclear)</li>
            <li><strong>Data Assessment:</strong> Image contains genuine flags worthy of classification</li>
        </ul>
        <p><strong>Click the decision buttons</strong> to record your assessment for each image.</p>
    </div>

    <div class="summary">
        <h3>📊 Summary</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
            <div style="text-align: center; padding: 15px; background: #ffebee; border-radius: 6px;">
                <div style="font-size: 2em; font-weight: bold; color: #d32f2f;">${barryReviewClassifications.length}</div>
                <div>Disputed Images</div>
            </div>
            <div style="text-align: center; padding: 15px; background: #e8f5e8; border-radius: 6px;">
                <div style="font-size: 2em; font-weight: bold; color: #388e3c;" id="barry-correct">0</div>
                <div>Barry Correct</div>
            </div>
            <div style="text-align: center; padding: 15px; background: #fff3e0; border-radius: 6px;">
                <div style="font-size: 2em; font-weight: bold; color: #f57c00;" id="data-correct">0</div>
                <div>Data Correct</div>
            </div>
            <div style="text-align: center; padding: 15px; background: #f3e5f5; border-radius: 6px;">
                <div style="font-size: 2em; font-weight: bold; color: #7b1fa2;" id="unclear-count">0</div>
                <div>Unclear/Need Discussion</div>
            </div>
        </div>
        <div class="progress">
            <div class="progress-bar" id="progress-bar"></div>
        </div>
        <div style="text-align: center; margin-top: 10px;">
            <span id="progress-text">0 of ${barryReviewClassifications.length} images reviewed</span>
        </div>
    </div>

    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h3>📊 False Positive Data Analysis</h3>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div>
                <h4>Dataset Overview</h4>
                <ul>
                    <li><strong>Total images processed:</strong> ${falsePositiveData.data_summary.total_images.toLocaleString()}</li>
                    <li><strong>CV-positive images:</strong> ${falsePositiveData.data_summary.cv_positive_images.toLocaleString()} (flags detected, sent for expert review)</li>
                    <li><strong>CV-negative images:</strong> ${falsePositiveData.data_summary.cv_negative_images.toLocaleString()} (no flags detected, not reviewed)</li>
                    <li><strong>True positives:</strong> ${falsePositiveData.data_summary.true_positives.toLocaleString()} (expert confirmed flags are genuine)</li>
                    <li><strong>False positives:</strong> ${falsePositiveData.data_summary.false_positives.toLocaleString()} (expert rejected detected flags)</li>
                    <li><strong>Positive Predictive Value:</strong> ${Math.round((falsePositiveData.data_summary.true_positives / (falsePositiveData.data_summary.true_positives + falsePositiveData.data_summary.false_positives)) * 100)}% (${falsePositiveData.data_summary.true_positives}/${falsePositiveData.data_summary.true_positives + falsePositiveData.data_summary.false_positives})</li>
                    <li><em>Note: True/False negatives cannot be determined as CV-negative images were not expert reviewed</em></li>
                </ul>
            </div>
            <div>
                <h4>Key Statistics</h4>
                <p><strong>Original CV Results (flags):</strong></p>
                <ul>
                    ${Object.entries(falsePositiveData.data_summary.flags_distribution)
                      .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                      .map(([flag, count]) => 
                        `<li>flags = ${flag}: ${count.toLocaleString()} images</li>`
                      ).join('')}
                </ul>
            </div>
        </div>

        <div style="margin-bottom: 20px;">
            <h4>🚨 Disputed Records - These are the exact entries from your false positive data:</h4>
            <div style="overflow-x: auto; background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #ff5722;">
                <table style="width: 100%; border-collapse: collapse; font-family: monospace; font-size: 0.9em;">
                    <thead>
                        <tr style="background: #e3f2fd;">
                            ${falsePositiveData.columns.map(col => 
                              `<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">${col}</th>`
                            ).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${falsePositiveData.disputed_data.map(row => `
                            <tr style="background: ${row.indicator === '1.0' ? '#ffecec' : '#fff'};">
                                ${falsePositiveData.columns.map(col => 
                                  `<td style="border: 1px solid #ddd; padding: 8px;">
                                    ${col === 'indicator' && row[col] === null ? 
                                      '<span style="color: #666; font-style: italic;">NaN</span>' : 
                                      row[col] || ''}
                                  </td>`
                                ).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <p style="margin-top: 10px; font-size: 0.9em; color: #666;">
                <strong>Key:</strong> 
                <span style="background: #ffecec; padding: 2px 4px; border-radius: 3px;">Red rows</span> = 
                Marked as "true positive" (indicator = 1.0) in false positive data, but Barry flagged for review
            </p>
        </div>

        <details style="background: #f0f7ff; padding: 15px; border-radius: 6px; margin-top: 20px;">
            <summary style="cursor: pointer; font-weight: bold; color: #1976d2;">
                📋 Sample of Original Dataset (click to expand)
            </summary>
            <div style="overflow-x: auto; margin-top: 15px;">
                <table style="width: 100%; border-collapse: collapse; font-family: monospace; font-size: 0.8em;">
                    <thead>
                        <tr style="background: #e1f5fe;">
                            ${falsePositiveData.columns.map(col => 
                              `<th style="border: 1px solid #ddd; padding: 6px; text-align: left;">${col}</th>`
                            ).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${falsePositiveData.sample_data.slice(0, 20).map(row => `
                            <tr>
                                ${falsePositiveData.columns.map(col => 
                                  `<td style="border: 1px solid #ddd; padding: 6px;">
                                    ${col === 'indicator' && row[col] === null ? 
                                      '<span style="color: #666; font-style: italic;">NaN</span>' : 
                                      row[col] || ''}
                                  </td>`
                                ).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <p style="margin-top: 10px; font-size: 0.8em; color: #666;">
                    Showing 20 of ${falsePositiveData.sample_data.length} sample records from the full dataset.
                </p>
            </div>
        </details>
    </div>

    ${barryReviewClassifications.map((classification, index) => {
      const baseFilename = extractBaseFilename(classification.image_id);
      // Use the original panoramic image instead of the cropped version
      const imageUrl = `../public/images/ENNISKILLEN/${baseFilename}.jpg`;
      const isInData = falsePositiveData.true_positives.includes(baseFilename);
      
      return `
    <div class="dispute-item" id="dispute-${index}">
        <div class="dispute-header">
            <h3>🚨 Dispute #${index + 1}: ${classification.image_id}</h3>
            <div class="metadata">
                <strong>Base filename:</strong> ${baseFilename} | 
                <strong>Date flagged:</strong> ${new Date(classification.timestamp).toLocaleDateString()} | 
                <span class="conflict-badge">CONFLICT</span>
            </div>
        </div>
        
        <div class="dispute-content">
            <div class="assessment-panel barry-assessment">
                <h4>🙋‍♂️ Barry's Assessment</h4>
                <p><strong>Classification:</strong> Review/False Positive</p>
                <p><strong>Reason:</strong> "${classification.review_reason || 'Not specified'}"</p>
                <p><strong>Barry's view:</strong> This image should NOT be shown to experts for classification</p>
            </div>
            
            <div class="assessment-panel data-assessment">
                <h4>📊 False Positive Data Assessment</h4>
                <p><strong>Classification:</strong> True Positive</p>
                <p><strong>Status:</strong> ${isInData ? 'Contains genuine flags' : 'Not found in dataset'}</p>
                <p><strong>Data view:</strong> This image SHOULD be shown to experts for classification</p>
            </div>
            
            <div class="image-container">
                <h4>🖼️ Images for Review</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div>
                        <h5>📸 Original Panoramic Image</h5>
                        <img src="${imageUrl}" alt="Original panoramic image ${baseFilename}.jpg" class="dispute-image" 
                             onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22200%22><rect width=%22100%25%22 height=%22100%25%22 fill=%22%23f0f0f0%22/><text x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 fill=%22%23666%22>Image not found: ${baseFilename}.jpg</text></svg>'">
                        <p style="text-align: center; margin-top: 10px; font-size: 0.9em; color: #666;">
                            <strong>Full Context:</strong> ${baseFilename}.jpg
                        </p>
                    </div>
                    <div>
                        <h5>🎯 Cropped Flag Region (Barry's Classification)</h5>
                        <img src="../public/images/ENNISKILLEN/${classification.image_id}" alt="Cropped flag region ${classification.image_id}" class="dispute-image" 
                             onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22200%22><rect width=%22100%25%22 height=%22100%25%22 fill=%22%23f0f0f0%22/><text x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 fill=%22%23666%22>Image not found: ${classification.image_id}</text></svg>'">
                        <p style="text-align: center; margin-top: 10px; font-size: 0.9em; color: #666;">
                            <strong>Barry's Focus:</strong> ${classification.image_id}
                        </p>
                    </div>
                </div>
                <div class="metadata">
                    <p><strong>Original File:</strong> ${baseFilename}.jpg</p>
                    <p><strong>Barry's Disputed Cropped File:</strong> ${classification.image_id}</p>
                    <p><strong>Location:</strong> public/images/ENNISKILLEN/</p>
                </div>
            </div>
            
            <div class="decision-area">
                <h4>✅ Your Decision</h4>
                <p>After examining the image, who is correct?</p>
                <div class="decision-buttons">
                    <button class="btn btn-barry" onclick="makeDecision(${index}, 'barry')">
                        Barry is Correct (False Positive)
                    </button>
                    <button class="btn btn-data" onclick="makeDecision(${index}, 'data')">
                        Data is Correct (True Positive)
                    </button>
                    <button class="btn btn-unclear" onclick="makeDecision(${index}, 'unclear')">
                        Unclear - Needs Discussion
                    </button>
                </div>
                <div id="decision-${index}" style="margin-top: 10px; font-weight: bold;"></div>
                <textarea id="notes-${index}" placeholder="Notes/reasoning for this decision..." 
                         style="width: 100%; margin-top: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 4px;"></textarea>
            </div>
        </div>
    </div>
      `;
    }).join('')}

    <div class="navigation">
        <h4>📋 Review Summary</h4>
        <div id="completion-status">
            <p id="decisions-summary">Review images above to see summary</p>
        </div>
        <button onclick="exportDecisions()" style="width: 100%; padding: 10px; background: #2196f3; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;">
            📥 Export Decisions
        </button>
        <button onclick="window.print()" style="width: 100%; padding: 10px; background: #4caf50; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 5px;">
            🖨️ Print Report
        </button>
    </div>

    <script>
        let decisions = {};
        
        function makeDecision(index, decision) {
            decisions[index] = {
                decision: decision,
                timestamp: new Date().toISOString(),
                notes: document.getElementById('notes-' + index).value
            };
            
            const decisionElement = document.getElementById('decision-' + index);
            const colors = {
                barry: '#4caf50',
                data: '#ff9800', 
                unclear: '#9e9e9e'
            };
            const texts = {
                barry: '✅ Barry Correct - Update false positive data',
                data: '✅ Data Correct - Provide feedback to Barry',
                unclear: '❓ Unclear - Schedule discussion'
            };
            
            decisionElement.style.color = colors[decision];
            decisionElement.textContent = texts[decision];
            
            updateSummary();
            updateProgress();
        }
        
        function updateSummary() {
            const counts = { barry: 0, data: 0, unclear: 0 };
            Object.values(decisions).forEach(d => counts[d.decision]++);
            
            document.getElementById('barry-correct').textContent = counts.barry;
            document.getElementById('data-correct').textContent = counts.data;
            document.getElementById('unclear-count').textContent = counts.unclear;
        }
        
        function updateProgress() {
            const total = ${barryReviewClassifications.length};
            const completed = Object.keys(decisions).length;
            const percentage = (completed / total) * 100;
            
            document.getElementById('progress-bar').style.width = percentage + '%';
            document.getElementById('progress-text').textContent = completed + ' of ' + total + ' images reviewed';
            
            if (completed === total) {
                document.getElementById('completion-status').innerHTML = 
                    '<p style="color: #4caf50; font-weight: bold;">✅ Review Complete!</p>' +
                    '<p>All disputes have been reviewed. Export your decisions below.</p>';
            }
        }
        
        function exportDecisions() {
            const exportData = {
                review_metadata: {
                    reviewer: prompt('Enter your name/ID for the review:') || 'Anonymous',
                    review_date: new Date().toISOString(),
                    total_disputes: ${barryReviewClassifications.length},
                    decisions_made: Object.keys(decisions).length
                },
                disputed_images: ${JSON.stringify(barryReviewClassifications.map((c, i) => ({
                  index: i,
                  image_id: c.image_id,
                  base_filename: extractBaseFilename(c.image_id),
                  barry_reason: c.review_reason,
                  timestamp: c.timestamp
                })))},
                expert_decisions: decisions
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'expert-review-decisions-' + new Date().toISOString().split('T')[0] + '.json';
            a.click();
            URL.revokeObjectURL(url);
        }
        
        // Auto-save to localStorage
        setInterval(() => {
            localStorage.setItem('expertReviewDecisions', JSON.stringify(decisions));
        }, 30000);
        
        // Load saved decisions on page load
        window.onload = function() {
            const saved = localStorage.getItem('expertReviewDecisions');
            if (saved) {
                try {
                    decisions = JSON.parse(saved);
                    Object.keys(decisions).forEach(index => {
                        const decision = decisions[index];
                        document.getElementById('decision-' + index).style.color = 
                            decision.decision === 'barry' ? '#4caf50' : 
                            decision.decision === 'data' ? '#ff9800' : '#9e9e9e';
                        document.getElementById('decision-' + index).textContent = 
                            decision.decision === 'barry' ? '✅ Barry Correct - Update false positive data' :
                            decision.decision === 'data' ? '✅ Data Correct - Provide feedback to Barry' :
                            '❓ Unclear - Schedule discussion';
                        if (decision.notes) {
                            document.getElementById('notes-' + index).value = decision.notes;
                        }
                    });
                    updateSummary();
                    updateProgress();
                } catch (e) {
                    console.log('Could not load saved decisions');
                }
            }
        };
    </script>
</body>
</html>
    `;
    
    // Step 4: Write HTML file
    const reportPath = 'scripts/visual-discrepancy-report.html';
    fs.writeFileSync(reportPath, htmlContent);
    
    console.log(`   ✅ Visual report created: ${reportPath}`);
    
    // Step 5: Try to open the report
    console.log('\n4️⃣ Opening report in browser...');
    try {
      const { execSync } = await import('child_process');
      const fullPath = path.resolve(reportPath);
      
      // Try to open in default browser (cross-platform)
      try {
        execSync(`open "${fullPath}"`, { stdio: 'ignore' }); // macOS
      } catch {
        try {
          execSync(`start "${fullPath}"`, { stdio: 'ignore' }); // Windows
        } catch {
          try {
            execSync(`xdg-open "${fullPath}"`, { stdio: 'ignore' }); // Linux
          } catch {
            console.log('   ⚠️  Could not auto-open browser. Please open manually.');
          }
        }
      }
      
      console.log(`   🌐 Report should open in your default browser`);
      console.log(`   📂 Manual path: ${fullPath}`);
      
    } catch (error) {
      console.log('   ⚠️  Could not auto-open browser. Please open manually.');
    }
    
    console.log('\n5️⃣ NEXT STEPS');
    console.log('=' .repeat(50));
    console.log('📋 Share this HTML report with your colleague:');
    console.log(`   • File: ${reportPath}`);
    console.log('   • The report is interactive and self-contained');
    console.log('   • Your colleague can make decisions directly in the browser');
    console.log('   • Decisions can be exported as JSON for further processing');
    console.log('   • The report auto-saves progress to browser localStorage');
    console.log();
    console.log('🔍 Review Process:');
    console.log('   1. Colleague examines each disputed image visually');
    console.log('   2. Compares Barry\'s reason vs. false positive data classification');
    console.log('   3. Makes expert decision on who is correct');
    console.log('   4. Exports decisions as JSON file');
    console.log('   5. You can use the JSON to update false positive data or provide feedback');
    
  } catch (error) {
    console.error('❌ Error creating visual report:', error);
  }
}

// Run the script
createVisualDiscrepancyReport().catch(console.error); 