# Flag Classification Training Workflow Documentation

## 📋 **Overview**

This document outlines the complete workflow for training flag classification models, including data consolidation, training procedures, validation methods, and critical bug fixes discovered during development.

> **📊 Centralized Results**: All experiment results and performance comparisons are documented in [`experiments/results_summary.md`](experiments/results_summary.md)

## 🏗️ **System Architecture**

### **Core Components**
1. **Dataset Management**: Multiple consolidation levels (70 → 16 → 7 classes)
2. **Training Framework**: Dassl + CoCoOp + CLIP with MPS acceleration
3. **Validation Pipeline**: Per-class metrics and comprehensive analysis
4. **Configuration Management**: YAML-based dataset and trainer configs

### **Data Flow**
```
Raw Images (70 classes) 
    ↓ [consolidation_script.py]
16-Class Consolidated Dataset
    ↓ [super_consolidate.py]  
7-Class Super-Consolidated Dataset
    ↓ [train_minimal_mps.py]
Trained Models + Evaluation Results
```

## 🔄 **Complete Workflow Steps**

### **Phase 1: Data Preparation & Analysis**
1. **Initial Analysis**
   ```bash
   python analyze_class_distribution.py
   ```
   - Analyze original 70-class distribution
   - Identify class imbalance issues (800:1 ratio)
   - Generate consolidation recommendations

2. **Class Consolidation** (70 → 16 classes)
   ```bash
   python consolidation_script.py
   ```
   - **Input**: Original 70 hierarchical classes
   - **Output**: 16 economically-relevant consolidated classes
   - **Key Fix**: Corrected JSON key access bug (`dataset_overview` vs `statistics`)

3. **Super-Consolidation** (16 → 7 classes) - Optional
   ```bash
   python scripts/super_consolidate.py
   ```
   - **Input**: 16 consolidated classes
   - **Output**: 7 super-consolidated classes
   - **Purpose**: Address severe class imbalance

### **Phase 2: Training Configuration**

4. **Dataset Registration**
   - Create dataset classes: `ni_flags_consolidated.py`, `ni_flags_super_consolidated.py`
   - Register with Dassl framework
   - Create YAML configs: `niflags_consolidated.yaml`, `niflags_super_consolidated.yaml`

5. **Training Script Setup**
   ```bash
   # Import dataset classes in train_minimal_mps.py
   import datasets.ni_flags_consolidated
   import datasets.ni_flags_super_consolidated
   ```

### **Phase 3: Model Training**

6. **Training Execution**
   ```bash
   # 16-class consolidated
   python train_minimal_mps.py --clean --trainer CoCoOp \
       --config-file configs/trainers/CoCoOp/vit_b32.yaml \
       --dataset-config-file configs/datasets/niflags_consolidated.yaml \
       --output-dir experiments/vit_b32_consolidated \
       TRAINER.COCOOP.PREC fp32 DATALOADER.NUM_WORKERS 0 OPTIM.MAX_EPOCH 100
   
   # 7-class super-consolidated
   python train_minimal_mps.py --clean --trainer CoCoOp \
       --config-file configs/trainers/CoCoOp/vit_b32.yaml \
       --dataset-config-file configs/datasets/niflags_super_consolidated.yaml \
       --output-dir experiments/vit_b32_super_consolidated \
       TRAINER.COCOOP.PREC fp32 DATALOADER.NUM_WORKERS 0 OPTIM.MAX_EPOCH 100
   ```

### **Phase 4: Validation & Analysis**

7. **Performance Analysis**
   ```bash
   python scripts/analyze_predictions.py
   python evaluate_consolidated.py
   ```
   - Per-class accuracy analysis
   - Confusion matrix generation
   - Prediction pattern diagnosis

## 🚨 **Critical Bug Fixes Discovered**

### **Bug 1: JSON Key Access Error** (consolidation_script.py)
```python
# WRONG (caused KeyError)
report.append(f"Total classes: {orig_dist['statistics']['unique_hierarchical_classes']}")

# FIXED
dataset_overview = original_stats['dataset_overview']
orig_stats = orig_dist['statistics']
report.append(f"Total classes: {dataset_overview['unique_hierarchical_classes']}")
```

### **Bug 2: Hardcoded Class Weights** (trainers/cocoop.py)
```python
# WRONG (caused training failure)
dataset_info_path = Path("../data/ni_flags_v2/dataset_info.json")  # Hardcoded wrong dataset!

# FIXED
# Disabled hardcoded weights, use uniform weights
return torch.ones(num_classes)
```

**Impact**: This bug caused:
- 7-class training to fail completely (4.35 loss, no learning)
- 16-class training to use wrong weights (may have affected 52.5% accuracy)
- All training runs to potentially use incorrect class distributions

## 📊 **Performance Results Summary**

| **Approach** | **Classes** | **Accuracy** | **Macro-F1** | **Issues** |
|--------------|-------------|--------------|--------------|------------|
| **Original** | 70 classes | ~15% | ~3% | Severe class imbalance (800:1) |
| **16-Class Consolidated** | 16 classes | 52.5% | 8.4% | Wrong weights bug, but best performance |
| **7-Class Super-Consolidated (Buggy)** | 7 classes | 6.8% | 4.5% | Training failure due to wrong weights |
| **7-Class Super-Consolidated (Fixed)** | 7 classes | 2.6% | 2.1% | Still extreme imbalance (85.8% in one class) |

## 🎯 **Key Insights**

### **Why 16-Class Works Better**
1. **Balanced consolidation**: 75.5% dominant class vs 85.8% in 7-class
2. **Meaningful distinctions**: Preserves impact-level differences (High/Medium/Low)
3. **Learning complexity**: Sweet spot between too many (70) and too few (7) classes

### **Class Distribution Analysis**
```
16-Class: Unionist_High_Impact (75.5%) + 7 other classes >1%
7-Class:  Unionist_All (85.8%) + only 3 other classes >1%
```

## 🔧 **Dynamic Improvements Needed**

### **Current Issues**
1. **Hardcoded dataset paths** in class weight loading
2. **Manual dataset registration** required for each consolidation level
3. **No automatic class weight calculation** from current dataset
4. **Static configuration files** don't adapt to dataset changes

### **Proposed Dynamic Solutions**
1. **Auto-detect dataset structure** and calculate weights dynamically
2. **Generic dataset factory** that adapts to any consolidation level
3. **Automatic config generation** based on dataset analysis
4. **Runtime class balancing** options (weighted sampling, focal loss tuning)

## 📝 **Configuration Files Structure**

### **Dataset Configs**
```yaml
# configs/datasets/niflags_consolidated.yaml
DATASET:
  NAME: "NIFlagsConsolidated"
  ROOT: "../data"
  NUM_SHOTS: -1  # Use all data
```

### **Trainer Configs**
```yaml
# configs/trainers/CoCoOp/vit_b32.yaml
TRAINER:
  NAME: "CoCoOp"
  COCOOP:
    N_CTX: 16
    PREC: "fp32"
OPTIM:
  MAX_EPOCH: 100
  LR: 0.002
```

## 🚀 **Future Development Priorities**

### **Immediate Fixes**
1. ✅ Fix hardcoded class weights bug
2. ⏳ Implement dynamic weight calculation
3. ⏳ Create generic dataset factory
4. ⏳ Add balanced sampling options

### **Advanced Features**
1. **Automatic hyperparameter tuning** based on class distribution
2. **Multi-level ensemble** combining different consolidation approaches
3. **Active learning** for difficult minority classes
4. **Real-time training monitoring** with early stopping

## 📊 **Validation Methodology**

### **Metrics Used**
- **Overall Accuracy**: Correct predictions / Total predictions
- **Macro-F1**: Average F1 across all classes (handles imbalance)
- **Per-Class Accuracy**: Individual class performance
- **Confusion Matrix**: Class-wise prediction patterns

### **Evaluation Scripts**
1. `analyze_predictions.py`: Prediction pattern analysis
2. `evaluate_consolidated.py`: Comprehensive per-class metrics
3. Training logs: Real-time loss and accuracy tracking

## 📂 **File Structure**
```
flag_classification_adaptation/
├── consolidation_script.py          # 70→16 class consolidation
├── scripts/
│   ├── super_consolidate.py         # 16→7 class consolidation
│   └── analyze_predictions.py       # Prediction analysis
├── datasets/
│   ├── ni_flags_consolidated.py     # 16-class dataset
│   └── ni_flags_super_consolidated.py # 7-class dataset
├── configs/
│   ├── datasets/                    # Dataset configurations
│   └── trainers/                    # Trainer configurations
├── trainers/
│   └── cocoop.py                    # Modified CoCoOp trainer
├── train_minimal_mps.py             # Main training script
├── evaluate_consolidated.py         # Validation script
└── experiments/                     # Training outputs
```

## 🎯 **Recommended Workflow for Future Runs**

1. **Always check for bugs** in class weight loading
2. **Validate dataset distribution** before training
3. **Use consistent evaluation metrics** across all approaches
4. **Document configuration changes** and their impact
5. **Compare results** only after ensuring identical conditions

This workflow documentation should serve as the foundation for reproducible experiments and future development of the flag classification system.