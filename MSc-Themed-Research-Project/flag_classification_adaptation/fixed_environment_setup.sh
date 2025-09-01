#!/bin/bash
# Fixed Environment Setup for Flag Classification on M4 Max

echo "🔧 Setting up corrected conda environment for flag classification..."

# Ensure we're in the right conda environment
if [[ "$CONDA_DEFAULT_ENV" != "flag_classification" ]]; then
    echo "Please activate the environment first:"
    echo "conda activate flag_classification"
    exit 1
fi

echo "✅ Using conda environment: $CONDA_DEFAULT_ENV"

# Install DaSsL from source (required for Li et al.'s code)
echo "📦 Installing DaSsL from source..."
pip install git+https://github.com/KaiyangZhou/Dassl.pytorch.git

# Install other required packages
echo "📦 Installing additional dependencies..."
pip install ftfy regex tqdm
pip install open-clip-torch
pip install timm
pip install yacs
pip install tensorboard

# Install data processing dependencies
pip install pandas numpy pillow
pip install scikit-learn matplotlib seaborn

# Install Jupyter for analysis (optional but useful)
pip install jupyter ipykernel

# Verify installations
echo "🧪 Verifying installations..."

python3 -c "
import sys
print(f'Python version: {sys.version}')

try:
    import torch
    print(f'✅ PyTorch {torch.__version__} installed')
    print(f'✅ MPS available: {torch.backends.mps.is_available()}')
except ImportError as e:
    print(f'❌ PyTorch import failed: {e}')

try:
    import torchvision
    print(f'✅ TorchVision {torchvision.__version__} installed')
except ImportError as e:
    print(f'❌ TorchVision import failed: {e}')

try:
    from dassl.config import get_cfg_default
    print('✅ DaSsL installed successfully')
except ImportError as e:
    print(f'❌ DaSsL import failed: {e}')

try:
    import clip
    print('✅ CLIP available')
except ImportError as e:
    print(f'❌ CLIP import failed: {e}')

try:
    import open_clip
    print('✅ OpenCLIP available')
except ImportError as e:
    print(f'❌ OpenCLIP import failed: {e}')

try:
    import timm
    print('✅ TIMM available')
except ImportError as e:
    print(f'❌ TIMM import failed: {e}')
"

echo ""
echo "🎉 Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Test basic functionality: python quick_test.py"
echo "2. Copy Li et al.'s code to your adaptation directory"
echo "3. Start implementing the flag classification modifications"
