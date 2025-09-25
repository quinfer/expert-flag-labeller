# Methodology Documentation

## Dataset Preparation

### Source Data
- **Origin**: GroundingDINO detection on 2M Google Street View images (2022-2023)
- **Expert Classifications**: 9,535 classifications across 3,354 unique images
- **Quality Control**: Confidence filtering ≥3.0 (1-5 scale)
- **Final Dataset**: 5,490 high-quality annotations

### Data Splits
- **Training**: 3,823 images (69.6%)
- **Validation**: 841 images (15.3%) 
- **Test**: 826 images (15.1%)
- **Total**: 5,490 images

## Economic Consolidation

### Original Structure
70 fine-grained classes: Category-Mount_type-Specific_flag
- Categories: National, Proscribed, International, Sport, Fraternal, Historical, Military
- Mount types: Building-mounted, Lamppost-mounted, Pole-mounted, Window display, etc.

### Consolidated Structure  
7 economic categories based on community impact:

1. **Major_Unionist** (2,047 samples) - Territorial signaling, coordination effects
2. **Cultural_Fraternal** (892 samples) - Heritage signaling, local coordination  
3. **International** (485 samples) - Tourism/trade connotations
4. **Nationalist** (354 samples) - Context-dependent territorial impact
5. **Paramilitary** (312 samples) - Security-related negative externalities
6. **Commemorative** (233 samples) - Tourism positive, context-sensitive
7. **Sport_Community** (178 samples) - Local economic benefit

### Concentration Metrics
- **Original Imbalance**: 169:1 ratio
- **Post-consolidation**: 8.8:1 ratio  
- **HHI Reduction**: To ~1,847 (near economic intervention threshold of 1,800)
- **Effective Classes**: Increased via N_eff = 1/HHI

## Model Architecture

### RS5M ViT-H-14
- **Base Model**: Vision Transformer pre-trained on remote sensing imagery
- **Rationale**: Spatial pattern recognition applicable to territorial markers
- **Architecture**: Hierarchical prompt tuning with economic category embeddings

### Training Configuration
- **Optimizer**: AdamW with differential learning rates
- **Batch Size**: 8 (hardware constrained)
- **Learning Rate**: 1e-4 
- **Epochs**: 30
- **Seeds**: 42, 123, 456 (reproducibility)
- **Augmentation**: Random crop, flip, colour jitter

## Key Results

### Performance Breakthrough
- **Baseline**: 0.56% accuracy (traditional approaches)
- **Economic Consolidation**: 94.78% accuracy
- **Improvement**: 169× performance gain

### Attention Analysis  
- **Baseline**: 23% attention on flag regions
- **Consolidated**: 87% attention on flag regions
- **Mechanism**: More efficient representational capacity allocation

### Statistical Validation
- **Multi-seed**: 94.57% ± 0.22% (seeds 42, 123, 456)
- **Cross-validation**: 93.23% ± 0.34% (5-fold stratified)
- **Macro-F1**: 67.45% (vs 15.2% baseline)
