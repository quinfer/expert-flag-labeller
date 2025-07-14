# False Positive Filtering Logic - Empirical Understanding

## 📋 **Data Flow Overview**

The false positive filtering system processes images through a specific pipeline that must be understood correctly to avoid misclassification.

### 🔄 **Processing Pipeline**

1. **Input Stage**: ~1.9M+ street-level images from all towns
2. **GroundingDINO Stage**: Images fed to GroundingDINO with prompt "flag"
3. **Algorithmic Classification**: GroundingDINO outputs `flags=1` for images it believes contain flags
4. **Expert Review Stage**: Human experts manually verify GroundingDINO's classifications
5. **Final Classification**: Expert produces `flags_correct=1` for true positives, `flags_correct=0` for false positives

## 🎯 **Critical Data Structure Understanding**

### **The Pickle File Structure**

Each town has three pickle files:
- `{TOWN}list.pickle`: List of all image paths processed
- `{TOWN}results.pickle`: Original GroundingDINO results (numpy array)
- `{TOWN}resultsCORRECT.pickle`: Expert-corrected results (pandas DataFrame)

### **The DataFrame Columns**

The `resultsCORRECT.pickle` contains:
- `f`: Image filename (without .jpg extension)
- `pano_id`: Panorama ID
- `flags`: GroundingDINO's classification (1 = flagged, 0 = not flagged)
- `flags_correct`: Expert's final classification (1 = true positive, 0 = false positive)
- `indicator`: Additional metadata

## ⚠️ **Common Misunderstanding (CRITICAL)**

### **❌ WRONG Logic:**
```
"False positives" = ALL images with flags_correct=0
```
This is **incorrect** because it includes:
- Images GroundingDINO never flagged (`flags=0`)
- Images that were correctly rejected by the algorithm

### **✅ CORRECT Logic:**
```
"False positives" = Images with flags=1 AND flags_correct=0
"True positives" = Images with flags=1 AND flags_correct=1
```

## 📊 **Classification Matrix**

| GroundingDINO (`flags`) | Expert Review (`flags_correct`) | Classification | Action |
|-------------------------|----------------------------------|----------------|---------|
| 0 | 0 | True Negative | Keep (not flagged) |
| 0 | 1 | False Negative | Keep (missed by algorithm) |
| 1 | 0 | **False Positive** | **Filter Out** |
| 1 | 1 | **True Positive** | **Keep** |

## 🔍 **Filtering Implementation**

### **What to Filter Out**
Only filter images where:
```python
(df['flags'] == 1) & (df['flags_correct'] == 0)
```

### **What to Keep**
Keep all images where:
```python
(df['flags'] == 1) & (df['flags_correct'] == 1)  # True positives
# OR
(df['flags'] == 0)  # Images never flagged by GroundingDINO
```

## 📈 **Expected Statistics**

Based on the correct understanding:

### **For ENNISKILLEN (Example)**
- Total images processed: ~33,864
- Images flagged by GroundingDINO: ~1,077 (`flags=1`)
- Expert-confirmed true positives: ~646 (`flags=1 AND flags_correct=1`)
- Actual false positives to filter: ~431 (`flags=1 AND flags_correct=0`)

### **False Positive Rate Calculation**
```
False Positive Rate = (flags=1 AND flags_correct=0) / (flags=1) * 100
For ENNISKILLEN: 431 / 1,077 = ~40% false positive rate
```

## 🚨 **Previous Error Analysis**

### **What Was Wrong**
The initial implementation incorrectly calculated:
- "False positives": 33,218 (97.7% of all images)
- This included 32,787 images that were never flagged by GroundingDINO

### **Why This Was Wrong**
- It conflated "not containing flags" with "false positive"
- True false positives are only images wrongly flagged by the algorithm
- The vast majority of images were correctly ignored by GroundingDINO

## 🎯 **Correct Implementation Requirements**

### **Filter Logic**
```python
# Load corrected data
df = pd.read_pickle(f"{town}resultsCORRECT.pickle")

# Identify actual false positives (algorithm was wrong)
false_positives = df[(df['flags'] == 1) & (df['flags_correct'] == 0)]

# Extract filenames for filtering
fp_filenames = [f"{row['f']}.jpg" for _, row in false_positives.iterrows()]
```

### **Expected Impact**
- Much smaller false positive count (hundreds, not hundreds of thousands)
- More reasonable false positive rates (30-50%, not 97%+)
- Preserved algorithm efficiency while filtering genuine mistakes

## 📝 **Documentation Notes**

- **Date**: July 11, 2025
- **Context**: Correction of major logic error in false positive filtering
- **Key Insight**: False positives are algorithmic mistakes, not absence of flags
- **Action Required**: Reprocess all town data with correct logic

## 🔄 **Next Steps**

1. **Reprocess all towns** with correct false positive identification
2. **Verify statistics** align with reasonable algorithmic performance
3. **Update filtering system** to use correct logic
4. **Test impact** on expert user experience

---

*This document serves as the definitive reference for understanding the false positive filtering logic in the Expert Flag Labeler system.* 