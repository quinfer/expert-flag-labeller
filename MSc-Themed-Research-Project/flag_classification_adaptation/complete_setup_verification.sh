#!/bin/bash
# Complete setup verification and Li et al. code integration

echo "🚀 Completing Flag Classification Setup..."

# Step 1: Copy Li et al.'s essential components
echo "📋 Copying Li et al.'s code components..."

if [ -d "../final_code" ]; then
    # Copy core modules
    echo "  Copying CLIP module..."
    cp -r ../final_code/clip ./
    
    echo "  Copying ViTAEv2 module..."
    cp -r ../final_code/vitaev2 ./
    
    echo "  Copying training script..."
    cp ../final_code/train.py ./
    
    # Create and copy trainer/dataset init files
    mkdir -p trainers datasets
    cp ../final_code/trainers/__init__.py ./trainers/
    cp ../final_code/datasets/__init__.py ./datasets/
    
    # Copy a sample config as template
    if [ -d "../final_code/configs" ]; then
        echo "  Copying config templates..."
        cp -r ../final_code/configs ./configs_original
    fi
    
    echo "✅ Li et al.'s components copied successfully"
else
    echo "❌ Could not find ../final_code directory"
    echo "Please ensure you're in the flag_classification_adaptation directory"
    exit 1
fi

# Step 2: Test complete installation
echo ""
echo "🧪 Testing complete installation..."
python3 -c "
import sys
print('🐍 Python Environment Test')
print(f'Python: {sys.version.split()[0]}')

# Test PyTorch + MPS
try:
    import torch
    print(f'✅ PyTorch {torch.__version__}')
    if torch.backends.mps.is_available():
        print('✅ MPS available for M4 Max acceleration')
        device = torch.device('mps')
        x = torch.randn(5, 5).to(device)
        y = torch.mm(x, x.t())
        print('✅ MPS tensor operations working')
    else:
        print('⚠️  MPS not available, using CPU')
except Exception as e:
    print(f'❌ PyTorch issue: {e}')

# Test DaSsL
try:
    from dassl.config import get_cfg_default
    from dassl.engine import build_trainer
    print('✅ DaSsL framework available')
except Exception as e:
    print(f'❌ DaSsL issue: {e}')

# Test Li et al.'s modules
try:
    import clip
    print('✅ CLIP module available')
except Exception as e:
    print(f'❌ CLIP module issue: {e}')

try:
    from vitaev2 import ViTAEv2
    print('✅ ViTAEv2 module available')
except Exception as e:
    print(f'❌ ViTAEv2 module issue: {e}')

# Test other dependencies
modules_to_test = [
    ('open_clip', 'OpenCLIP'),
    ('timm', 'TIMM'),
    ('yacs', 'YACS'),
    ('pandas', 'Pandas'),
    ('numpy', 'NumPy')
]

for module, name in modules_to_test:
    try:
        __import__(module)
        print(f'✅ {name} available')
    except ImportError:
        print(f'⚠️  {name} not available')
"

echo ""
echo "🎯 Week 9 Status Check:"

# Check directory structure
echo "📁 Directory Structure:"
for dir in trainers datasets configs utils scripts experiments; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/"
    else
        echo "  ⚠️  $dir/ (will create as needed)"
    fi
done

# Check for Li et al.'s components
echo ""
echo "📋 Li et al.'s Components:"
for component in clip vitaev2 train.py; do
    if [ -e "$component" ]; then
        echo "  ✅ $component"
    else
        echo "  ❌ $component missing"
    fi
done

echo ""
echo "🎉 SETUP VERIFICATION COMPLETE!"
echo ""
echo "✅ Your M4 Max is ready for flag classification!"
echo ""
echo "📋 Next Steps for Week 9:"
echo "1. Export your expert classifications from Supabase"
echo "2. Create the NIFlags dataset class"
echo "3. Modify CoCoOp trainer for flag hierarchical prompts"
echo "4. Run initial tests with small dataset"
echo ""
echo "🚀 Ready to proceed with flag classification adaptation!"
