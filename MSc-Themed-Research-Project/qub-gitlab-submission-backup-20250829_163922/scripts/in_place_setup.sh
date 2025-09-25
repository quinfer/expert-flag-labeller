#!/bin/bash
# In-Place Setup for Flag Classification within your existing MSc folder
# Run this from: /expert-flag-labeler/MSc-Themed-Research-Project/

echo "🚀 Setting up Flag Classification within your existing MSc project structure..."

# Check if we're in the right place
if [ ! -d "final_code" ]; then
    echo "❌ Error: Please run this from your MSc-Themed-Research-Project directory"
    echo "   Expected to find 'final_code' directory here"
    exit 1
fi

echo "✅ Found Li et al.'s code in final_code/"

# Create adaptation directory structure
echo "📁 Creating flag classification adaptation structure..."
mkdir -p flag_classification_adaptation/{datasets,trainers,configs/{datasets,trainers/CoCoOpFlags},utils,scripts,experiments/{week9_tests,baseline_results,final_models}}

# Copy base files from Li et al.'s code
echo "📋 Copying base files from Li et al.'s implementation..."
cp final_code/train.py flag_classification_adaptation/
cp final_code/requirements.txt flag_classification_adaptation/
cp -r final_code/clip flag_classification_adaptation/
cp -r final_code/vitaev2 flag_classification_adaptation/

# Copy existing configs as templates
cp final_code/configs/datasets/caltech101.yaml flag_classification_adaptation/configs/datasets/ni_flags.yaml
cp final_code/configs/trainers/CoCoOp/rn50_ep50.yaml flag_classification_adaptation/configs/trainers/CoCoOpFlags/

echo "🔧 Setting up data directory structure..."
mkdir -p data/{processed,annotations,images}

# Check if expert classifications exist
if [ -f "expert_classifications.json" ]; then
    echo "✅ Found expert classifications file"
    cp expert_classifications.json data/annotations/
elif [ -f "data/expert_classifications.json" ]; then
    echo "✅ Expert classifications already in data directory"
else
    echo "⚠️  Expert classifications not found - you'll need to add this file to data/annotations/"
fi

# Create environment setup
echo "🐍 Creating conda environment setup..."
cat > flag_classification_adaptation/setup_environment.sh << 'EOF'
#!/bin/bash
echo "Setting up conda environment for flag classification..."

# Create conda environment
conda create -n flag_classification python=3.10 -y
echo "Activating environment..."
conda activate flag_classification

# Install PyTorch with MPS support for M4 Max
pip3 install torch torchvision torchaudio

# Install project dependencies
pip install dassl-pytorch
pip install open-clip-torch
pip install timm
pip install yacs
pip install pandas numpy pillow
pip install scikit-learn matplotlib seaborn
pip install tensorboard

echo "✅ Environment setup complete!"
echo "To activate: conda activate flag_classification"
EOF

chmod +x flag_classification_adaptation/setup_environment.sh

# Create quick test script
echo "🧪 Creating quick test script..."
cat > flag_classification_adaptation/quick_test.py << 'EOF'
#!/usr/bin/env python3
"""
Quick test to verify M4 Max setup and basic functionality
"""
import torch
import sys
import os

def test_pytorch_mps():
    print("🔍 Testing PyTorch MPS Setup...")
    print(f"PyTorch version: {torch.__version__}")
    print(f"MPS available: {torch.backends.mps.is_available()}")
    print(f"MPS built: {torch.backends.mps.is_built()}")
    
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print(f"✅ Using device: {device}")
        
        # Test basic operations
        x = torch.randn(100, 100).to(device)
        y = torch.mm(x, x.t())
        print(f"✅ Matrix multiplication test passed: {y.shape}")
        
        return device
    else:
        print("⚠️  MPS not available, falling back to CPU")
        return torch.device("cpu")

def test_data_structure():
    print("\n📁 Testing data structure...")
    
    expected_paths = [
        "../data",
        "../data/annotations", 
        "../data/images",
        "../data/processed"
    ]
    
    for path in expected_paths:
        if os.path.exists(path):
            print(f"✅ Found: {path}")
        else:
            print(f"⚠️  Missing: {path}")

def test_imports():
    print("\n📦 Testing critical imports...")
    
    try:
        import clip
        print("✅ CLIP imported successfully")
    except ImportError as e:
        print(f"❌ CLIP import failed: {e}")
    
    try:
        import open_clip
        print("✅ OpenCLIP imported successfully")
    except ImportError as e:
        print(f"❌ OpenCLIP import failed: {e}")
    
    try:
        from dassl.config import get_cfg_default
        print("✅ DaSsL imported successfully")
    except ImportError as e:
        print(f"❌ DaSsL import failed: {e}")

if __name__ == "__main__":
    print("🚀 FLAG CLASSIFICATION QUICK TEST")
    print("=" * 50)
    
    device = test_pytorch_mps()
    test_data_structure() 
    test_imports()
    
    print("\n" + "=" * 50)
    print("✅ Quick test complete!")
    print("Next steps:")
    print("1. Run: conda activate flag_classification")
    print("2. Add your expert classifications to ../data/annotations/")
    print("3. Copy flag images to ../data/images/")
    print("4. Run data preparation script")
EOF

# Create data preparation script
echo "📊 Creating data preparation script..."
cat > flag_classification_adaptation/scripts/prepare_flag_data.py << 'EOF'
#!/usr/bin/env python3
"""
Data preparation script specifically for your expert flag annotations
"""
import json
import os
import shutil
from pathlib import Path

def prepare_flag_dataset():
    """Prepare flag dataset from your expert annotations"""
    
    # Paths relative to the flag_classification_adaptation directory
    base_dir = Path(__file__).parent.parent.parent  # Back to MSc project root
    data_dir = base_dir / "data"
    annotations_file = data_dir / "annotations" / "expert_classifications.json"
    
    print(f"Looking for annotations at: {annotations_file}")
    
    if not annotations_file.exists():
        print("❌ Expert classifications file not found!")
        print(f"Please add your expert_classifications.json to: {annotations_file}")
        return False
    
    # Load expert annotations
    with open(annotations_file, 'r') as f:
        annotations = json.load(f)
    
    print(f"✅ Loaded {len(annotations)} expert classifications")
    
    # Create processed annotations in the format expected by Li et al.'s code
    processed_annotations = {}
    
    for image_name, classification in annotations.items():
        # Create hierarchical classname: category-context-specific_flag
        hierarchical_name = f"{classification['category']}-{classification['context']}-{classification['specific_flag']}"
        hierarchical_name = hierarchical_name.replace(' ', '_').replace('-', '_')
        
        processed_annotations[image_name] = {
            'category': classification['category'],
            'context': classification['context'], 
            'specific_flag': classification['specific_flag'],
            'hierarchical_classname': hierarchical_name,
            'confidence': classification.get('confidence', 4.0)
        }
    
    # Save processed annotations
    processed_file = data_dir / "processed" / "processed_annotations.json"
    with open(processed_file, 'w') as f:
        json.dump(processed_annotations, f, indent=2)
    
    print(f"✅ Saved processed annotations to: {processed_file}")
    print(f"Example hierarchical classnames:")
    for i, (_, anno) in enumerate(processed_annotations.items()):
        if i < 5:  # Show first 5 examples
            print(f"  - {anno['hierarchical_classname']}")
    
    return True

if __name__ == "__main__":
    print("🎯 PREPARING FLAG DATASET")
    print("=" * 40)
    success = prepare_flag_dataset()
    if success:
        print("✅ Data preparation complete!")
    else:
        print("❌ Data preparation failed")
EOF

# Create README for the adaptation
echo "📖 Creating README..."
cat > flag_classification_adaptation/README.md << 'EOF'
# Flag Classification Adaptation

This directory contains the adaptation of Li et al.'s hierarchical prompt tuning for Northern Ireland flag classification.

## Quick Start

1. **Setup Environment:**
   ```bash
   ./setup_environment.sh
   conda activate flag_classification
   ```

2. **Test Setup:**
   ```bash
   python quick_test.py
   ```

3. **Prepare Data:**
   ```bash
   python scripts/prepare_flag_data.py
   ```

4. **Train Model:**
   ```bash
   python train.py \
     --trainer CoCoOpFlags \
     --dataset-config-file configs/datasets/ni_flags.yaml \
     --config-file configs/trainers/CoCoOpFlags/rn50_ep50.yaml \
     --output-dir experiments/week9_tests
   ```

## Directory Structure

- `datasets/` - Custom dataset classes
- `trainers/` - Modified trainers for flag classification  
- `configs/` - Configuration files for training
- `utils/` - Utility functions (M4 Max compatibility, etc.)
- `scripts/` - Data preparation and analysis scripts
- `experiments/` - Training outputs and results

## Key Adaptations

1. **Hierarchical Prompts:** Adapted from ship classification to flag categories
2. **M4 Max Compatibility:** MPS support for Apple Silicon
3. **Expert Annotations:** Integration with your existing 8,204 classifications
EOF

echo ""
echo "🎉 SETUP COMPLETE!"
echo ""
echo "Your flag classification adaptation is ready in:"
echo "  📁 flag_classification_adaptation/"
echo ""
echo "Next steps:"
echo "1. cd flag_classification_adaptation"
echo "2. ./setup_environment.sh"
echo "3. conda activate flag_classification" 
echo "4. python quick_test.py"
echo ""
echo "Your existing data structure is preserved:"
echo "  📁 final_code/           (Li et al.'s original - kept as reference)"
echo "  📁 data/                (Your expert annotations & images)"
echo "  📁 flag_classification_adaptation/  (Your working directory)"
echo ""
echo "🚀 Ready for Week 9 development!"
