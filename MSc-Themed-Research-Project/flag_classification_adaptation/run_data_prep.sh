#!/bin/bash
# Quick dataset preparation script

echo "========================================"
echo "🚀 PREPARING EXPANDED DATASET"
echo "========================================"
echo ""
echo "This script will:"
echo "1. Load classifications_0708.csv"
echo "2. Filter for confidence ≥3.0"
echo "3. Create train/val/test splits"
echo "4. Generate dataset structure"
echo ""

# Run the preparation script
python prepare_dataset_v2.py

# Check results
echo ""
echo "========================================"
echo "📊 CHECKING RESULTS"
echo "========================================"

if [ -d "../data/ni_flags_v2" ]; then
    echo "✅ Dataset created at ../data/ni_flags_v2"
    echo ""
    echo "Files created:"
    ls -la ../data/ni_flags_v2/*.txt 2>/dev/null
    echo ""
    
    # Count lines in each split
    if [ -f "../data/ni_flags_v2/train.txt" ]; then
        train_count=$(wc -l < ../data/ni_flags_v2/train.txt)
        echo "Training samples: $train_count"
    fi
    
    if [ -f "../data/ni_flags_v2/val.txt" ]; then
        val_count=$(wc -l < ../data/ni_flags_v2/val.txt)
        echo "Validation samples: $val_count"
    fi
    
    if [ -f "../data/ni_flags_v2/test.txt" ]; then
        test_count=$(wc -l < ../data/ni_flags_v2/test.txt)
        echo "Test samples: $test_count"
    fi
    
    if [ -f "../data/ni_flags_v2/classnames.txt" ]; then
        class_count=$(wc -l < ../data/ni_flags_v2/classnames.txt)
        echo "Number of classes: $class_count"
    fi
else
    echo "❌ Dataset directory not created"
fi

echo ""
echo "========================================"
echo "🎯 NEXT STEPS"
echo "========================================"
echo "1. Update dataset config to use ni_flags_v2"
echo "2. Run training with expanded dataset"
echo "3. Disable focal loss initially"
echo "4. Monitor improvements over baseline"
