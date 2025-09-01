#!/bin/bash
# Fix OpenMP conflicts for M4 Max PyTorch environment

echo "🔧 Fixing OpenMP conflicts for PyTorch on M4 Max..."

# Set environment variable permanently for this project
echo 'export KMP_DUPLICATE_LIB_OK=TRUE' >> ~/.zshrc
echo 'export OMP_NUM_THREADS=1' >> ~/.zshrc

# Also create a local .env file for the project
cat > .env << EOF
# OpenMP fix for M4 Max
export KMP_DUPLICATE_LIB_OK=TRUE
export OMP_NUM_THREADS=1

# MPS optimizations
export PYTORCH_ENABLE_MPS_FALLBACK=1
EOF

# Create a Python wrapper that always sets these
cat > run_training.sh << 'EOF'
#!/bin/bash
# Training wrapper with OpenMP fix

export KMP_DUPLICATE_LIB_OK=TRUE
export OMP_NUM_THREADS=1
export PYTORCH_ENABLE_MPS_FALLBACK=1

# Run the command passed as arguments
python "$@"
EOF

chmod +x run_training.sh

echo "✅ OpenMP fix applied!"
echo ""
echo "You can now run training in three ways:"
echo "1. Direct with fix: KMP_DUPLICATE_LIB_OK=TRUE python test_focal_loss.py"
echo "2. Using wrapper: ./run_training.sh test_focal_loss.py"
echo "3. Source environment: source .env && python test_focal_loss.py"
echo ""
echo "The fix has also been added to ~/.zshrc for future sessions"
