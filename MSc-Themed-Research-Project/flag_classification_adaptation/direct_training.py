#!/usr/bin/env python3
"""
Direct Training Script - Week 9
Bypasses shell issues and runs training directly in Python
"""

import os
import sys
import subprocess

def run_training():
    """Run the validation training directly"""
    
    print("🎯 STARTING DIRECT VALIDATION TRAINING")
    print("=" * 50)
    
    # Training parameters
    training_cmd = [
        sys.executable, "train_minimal.py",
        "--root", "../data",
        "--dataset-config-file", "configs/datasets/niflags.yaml", 
        "--config-file", "configs/trainers/CoCoOp/rn50.yaml",
        "--trainer", "CoCoOp",
        "--output-dir", "experiments/niflags_validation",
        "--seed", "1"
    ]
    
    # Add batch size and epochs for validation
    training_cmd.extend([
        "OPTIM.MAX_EPOCH", "5",
        "DATALOADER.TRAIN_X.BATCH_SIZE", "16"
    ])
    
    print("🚀 Running command:")
    print(" ".join(training_cmd))
    print()
    
    try:
        # Run training
        result = subprocess.run(training_cmd, check=True, capture_output=False)
        
        print("\n✅ VALIDATION TRAINING COMPLETE!")
        print("Check results in experiments/niflags_validation/")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Training failed with error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def check_environment():
    """Check if environment is set up correctly"""
    print("🔍 Checking environment...")
    
    # Check if we're in the right directory
    if not os.path.exists("train_minimal.py"):
        print("❌ train_minimal.py not found. Make sure you're in the flag_classification_adaptation directory")
        return False
    
    # Check if dataset exists
    if not os.path.exists("../data/ni_flags/annotations.json"):
        print("❌ Dataset not found. Run final_data_setup.py first")
        return False
    
    # Check if configs exist
    if not os.path.exists("configs/datasets/niflags.yaml"):
        print("❌ Dataset config not found")
        return False
    
    print("✅ Environment looks good!")
    return True

def main():
    print("🎯 DIRECT FLAG CLASSIFICATION TRAINING")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed")
        return
    
    # Run validation training
    success = run_training()
    
    if success:
        print("\n🎉 SUCCESS! Your training pipeline is working!")
        print("\nNext steps:")
        print("1. Check the results in experiments/niflags_validation/")
        print("2. If validation looks good, run full training")
        print("3. Proceed with Week 10 experiments")
    else:
        print("\n❌ Training failed. Check the error messages above.")

if __name__ == "__main__":
    main()
