# Dynamic Flag Classification System - Usage Guide

## 🚀 **Quick Start**

The dynamic system automatically handles different consolidation levels and class balancing strategies without hardcoded paths or manual configuration.

### **Basic Training Commands**

```bash
# 16-class with balanced weights (RECOMMENDED)
python train_dynamic.py \
    --config-file configs/trainers/CoCoOp/vit_b32.yaml \
    --class-balance-method inverse_frequency \
    --use-focal-loss \
    --clean \
    DATASET.NAME NIFlagsConsolidatedDynamic \
    OPTIM.MAX_EPOCH 50

# 16-class baseline (uniform weights)
python train_dynamic.py \
    --config-file configs/trainers/CoCoOp/vit_b32.yaml \
    --class-balance-method uniform \
    --clean \
    DATASET.NAME NIFlagsConsolidatedDynamic \
    OPTIM.MAX_EPOCH 50

# 7-class with aggressive balancing for extreme imbalance
python train_dynamic.py \
    --config-file configs/trainers/CoCoOp/vit_b32.yaml \
    --class-balance-method sqrt_inverse \
    --use-focal-loss \
    --focal-alpha 0.3 \
    --focal-gamma 2.0 \
    --clean \
    DATASET.NAME NIFlagsSuperConsolidatedDynamic \
    OPTIM.MAX_EPOCH 100
```

### **Comprehensive Comparison Study**

```bash
# Run all approaches and generate comparison report
python compare_approaches.py

# Quick comparison (essential approaches only)
python compare_approaches.py --quick

# Run single specific experiment
python compare_approaches.py --single 16class_balanced_focal
```

## 🎯 **Key Features Fixed**

### **1. Dynamic Class Weight Calculation**
- ✅ **No hardcoded dataset paths**
- ✅ **Automatic weight calculation** from current dataset
- ✅ **Multiple balancing strategies**: `uniform`, `inverse_frequency`, `sqrt_inverse`, `log_inverse`

### **2. Flexible Focal Loss**
- ✅ **Configurable parameters**: `--focal-alpha`, `--focal-gamma`
- ✅ **Automatic tuning** for different imbalance levels
- ✅ **Optional usage**: `--use-focal-loss` flag

### **3. Auto-Detection**
- ✅ **Dataset auto-detection** based on name
- ✅ **Automatic output directory** naming
- ✅ **Class distribution analysis** on load

## 📊 **Available Datasets**

| **Dataset Name** | **Classes** | **Description** |
|------------------|-------------|-----------------|
| `NIFlagsConsolidatedDynamic` | 16 classes | Economic consolidation (70→16) |
| `NIFlagsSuperConsolidatedDynamic` | 7 classes | Super consolidation (16→7) |
| `NIFlagsDynamic` | 70 classes | Original dataset |

## ⚖️ **Class Balancing Methods**

| **Method** | **Description** | **Best For** |
|------------|-----------------|--------------|
| `uniform` | Equal weights for all classes | Baseline comparison |
| `inverse_frequency` | Weight inversely proportional to frequency | Moderate imbalance (16-class) |
| `sqrt_inverse` | Square root of inverse frequency | Extreme imbalance (7-class) |
| `log_inverse` | Logarithmic inverse frequency | Very extreme imbalance |

## 🎛️ **Focal Loss Parameters**

| **Parameter** | **Default** | **Description** | **Tuning Guide** |
|---------------|-------------|-----------------|------------------|
| `focal_alpha` | 0.5 | Weight for rare classes | 0.3-0.7, lower for extreme imbalance |
| `focal_gamma` | 1.0 | Focus on hard examples | 1.0-2.0, higher for extreme imbalance |

## 📈 **Expected Performance**

Based on our analysis:

### **16-Class Consolidated** (RECOMMENDED)
- **Expected accuracy**: 55-65%
- **Expected macro-F1**: 15-25%
- **Best method**: `inverse_frequency` + focal loss
- **Training time**: ~2-3 minutes (50 epochs)

### **7-Class Super-Consolidated**
- **Expected accuracy**: 30-45%
- **Expected macro-F1**: 10-20%
- **Best method**: `sqrt_inverse` + aggressive focal loss
- **Training time**: ~3-4 minutes (100 epochs)

## 🔧 **Advanced Usage**

### **Custom Configuration**
```bash
python train_dynamic.py \
    --config-file configs/trainers/CoCoOp/vit_b32.yaml \
    --class-balance-method inverse_frequency \
    --use-focal-loss \
    --focal-alpha 0.4 \
    --focal-gamma 1.5 \
    --output-dir experiments/custom_experiment \
    --clean \
    DATASET.NAME NIFlagsConsolidatedDynamic \
    OPTIM.MAX_EPOCH 75 \
    OPTIM.LR 0.001 \
    DATALOADER.TRAIN_X.BATCH_SIZE 16
```

### **Evaluation Only**
```bash
python train_dynamic.py \
    --eval-only \
    --model-dir experiments/16class_balanced_focal \
    --config-file configs/trainers/CoCoOp/vit_b32.yaml \
    DATASET.NAME NIFlagsConsolidatedDynamic
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **"Dataset not found"**
   ```bash
   # Make sure data directories exist:
   ls ../data/ni_flags_consolidated/
   ls ../data/ni_flags_super_consolidated/
   ```

2. **"Registry conflict"**
   ```bash
   # Restart Python session or use different dataset names
   python -c "import sys; sys.exit(0)"  # Clean restart
   ```

3. **"Training stuck"**
   - Check if class weights are reasonable (should be 0.1-10.0 range)
   - Try different balancing method or disable focal loss
   - Verify dataset has correct annotations

### **Debug Mode**
```bash
# Add verbose logging
python train_dynamic.py \
    --config-file configs/trainers/CoCoOp/vit_b32.yaml \
    --class-balance-method uniform \
    DATASET.NAME NIFlagsConsolidatedDynamic \
    OPTIM.MAX_EPOCH 5 \
    VERBOSE True
```

## 📊 **Monitoring Training**

### **Real-time Monitoring**
```bash
# Watch training progress
tail -f experiments/your_experiment/log.txt

# Check GPU/MPS usage
python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

### **Result Analysis**
```bash
# Parse results automatically
python scripts/analyze_predictions.py --experiment-dir experiments/your_experiment

# Generate comprehensive report
python evaluate_consolidated.py --experiment-dir experiments/your_experiment
```

## 🎯 **Best Practices**

1. **Start with 16-class consolidated** - best balance of complexity and performance
2. **Use `inverse_frequency` weights** for moderate imbalance
3. **Enable focal loss** for better minority class learning
4. **Run comparison study** to find optimal configuration
5. **Monitor macro-F1** in addition to accuracy for imbalanced datasets
6. **Use `--clean` flag** to ensure fresh training runs

## 📁 **Output Structure**
```
experiments/
├── 16class_balanced_focal/           # Auto-generated names
│   ├── log.txt                       # Training logs
│   ├── tensorboard/                  # TensorBoard logs
│   └── prompt_learner/               # Model checkpoints
├── comparison_study/                 # Comparison results
│   ├── detailed_results.csv         # All metrics
│   ├── summary_report.md             # Human-readable summary
│   └── comparison_results.json       # Raw results
└── ...
```

This dynamic system eliminates the hardcoded bugs and provides flexible, reproducible training with automatic class balancing!