# CRITICAL BUG REPORT - Model Collapse to Majority Class

**Date**: January 13, 2025  
**Severity**: CRITICAL - Invalidates all reported results  
**Status**: DISCOVERED - Requires immediate fix  

## 🚨 Problem Summary

All RS5M experiments (baseline, hierarchical prompting, context ablations) achieved identical 72.63% accuracy because **all models collapsed to predicting only Class 13 (Commemorative_Historical)**, which represents 72.6% of the test set.

## 🔍 Evidence

### Identical Predictions Across All Experiments
- **Baseline RS5M**: 0.7262569832 accuracy
- **Hierarchical Prompting**: 0.7262569832 accuracy  
- **Context Ablations (all 3)**: 0.7262569832 accuracy
- **Prediction Analysis**: All models predict Class 13 for 100% of test samples

### Severe Class Imbalance
```
Class 13 (Commemorative_Historical): 260/358 samples (72.6%)
All other 15 classes combined:        98/358 samples (27.4%)
```

### Trivial Solution
- Models learned: "Always predict Class 13"
- Accuracy = Class 13 frequency = 72.63%
- **No actual classification learning occurred**

## 🧠 Root Cause Analysis

1. **Extreme Class Imbalance**: 72.6% vs 27.4% split
2. **Inadequate Loss Function**: Focal loss insufficient for this level of imbalance
3. **No Class Balancing**: Training dominated by majority class
4. **Model Collapse**: All architectures converged to trivial solution

## 📊 Academic Impact

### Invalidated Claims
- ❌ "72.63% accuracy breakthrough"
- ❌ "Hierarchical prompting maintains performance"  
- ❌ "Context ablations show optimal input representation"
- ❌ "4x improvement over baselines"

### Actual Status
- **Real performance**: Unknown (models never learned to classify)
- **All experiments**: Identical failure modes
- **Research contributions**: Currently invalid

## 🔧 Required Fixes

### Immediate Actions
1. **Implement proper class balancing**:
   - Balanced sampling during training
   - Class-weighted loss functions
   - Stratified evaluation metrics

2. **Fix evaluation metrics**:
   - Report per-class precision/recall
   - Use macro-averaged F1 (not accuracy)
   - Include confusion matrices

3. **Re-run all experiments** with proper balancing

### Technical Solutions
```python
# 1. Balanced Sampling
from torch.utils.data import WeightedRandomSampler
class_weights = compute_class_weights(train_labels)
sampler = WeightedRandomSampler(class_weights, len(train_dataset))

# 2. Class-Weighted Loss
class_weights = torch.tensor(compute_class_weights(train_labels))
criterion = nn.CrossEntropyLoss(weight=class_weights)

# 3. Proper Evaluation
from sklearn.metrics import classification_report
report = classification_report(y_true, y_pred, average=None)
```

## 📋 Recovery Plan

### Phase 1: Fix Training (1-2 days)
- [ ] Implement balanced sampling
- [ ] Add class-weighted loss
- [ ] Verify training sees all classes

### Phase 2: Re-run Experiments (3-4 days)  
- [ ] Baseline RS5M with proper balancing
- [ ] Hierarchical prompting with balancing
- [ ] Context ablations with balancing

### Phase 3: Proper Evaluation (1 day)
- [ ] Per-class metrics
- [ ] Confusion matrices  
- [ ] Statistical significance testing

## 🎓 Academic Learning

This is actually a **valuable learning experience** for your MSc:

1. **Statistical Intuition**: You correctly identified suspicious results
2. **Debugging Skills**: Systematic investigation revealed the root cause
3. **ML Best Practices**: Understanding class imbalance challenges
4. **Research Integrity**: Discovering and addressing fundamental issues

## 📝 Documentation Updates Needed

1. **Progress Report**: Mark current results as "Under Investigation"
2. **Supervisor Update**: Inform about discovery and recovery plan
3. **Methodology**: Add proper class balancing procedures

## 🚀 Next Steps

1. **Immediate**: Implement class balancing fixes
2. **Short-term**: Re-run experiments with proper methodology  
3. **Medium-term**: Document lessons learned for thesis
4. **Long-term**: This becomes a strength showing rigorous research practices

---

**This discovery demonstrates excellent research practices and statistical thinking. The fix will lead to much more meaningful and publishable results.**