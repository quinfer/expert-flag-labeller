# Disputed Images - Original Pickle File Data
## ENNISKILLEN False Positive Data for Barry's Disputed Images

### 📊 Overview
This package contains the original pickle file data (ENNISKILLENresultsCORRECT.pickle) filtered to show only the 19 images that Barry marked for review.

### 🔍 The Data
- **Source**: ENNISKILLENresultsCORRECT.pickle
- **Disputed Images**: 19 base filenames
- **CSV Records**: 19 rows (includes different angles/crops of same panoramic images)
- **Columns**: f, pano_id, flags, indicator, flags_correct

### 📁 Package Contents

#### Files
- `disputed_images_pickle_data.csv` - Original pickle data for disputed images (19 rows)
- `summary.json` - Metadata and statistics
- `images/` - All relevant image files (57 images)
- `README.md` - This documentation

#### Image Types
For each disputed case, you'll find:
- `[basename].jpg` - Original panoramic street view
- `[basename]_box0.jpg` - Cropped flag region (Barry's focus)
- `expert_confirmed_[basename].jpg` - Expert-confirmed version (if available)

### 📋 CSV Structure
The CSV file contains the original pickle file columns:

| Column | Description |
|--------|-------------|
| f | Base filename (panoramic image identifier) |
| pano_id | Panoramic image ID |
| flags | Number of flags detected by CV |
| indicator | 1.0 = show to experts, NaN = don't show |
| flags_correct | Expert verification (1 = correct, 0 = incorrect) |

### 🎯 Key Insights
- All disputed images have `indicator = 1.0` (marked to show to experts)
- All disputed images have `flags_correct = 1` (experts confirmed as genuine flags)
- Barry flagged these 19 images as false positives despite expert confirmation

### 📈 Context
- Part of 33864 total images in pickle file
- 793 images were expert-confirmed in total
- These 19 represent 2.4% of all expert-confirmed images

### 🔬 Analysis Usage
1. Load `disputed_images_pickle_data.csv` in your preferred analysis tool
2. Cross-reference with images in the `images/` folder
3. Compare Barry's field assessment with original expert confirmation
4. Identify patterns in disputed flag types or image characteristics

Generated: 2025-07-11T11:17:55.913Z
