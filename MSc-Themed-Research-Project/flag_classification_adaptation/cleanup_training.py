#!/usr/bin/env python3
"""
Training cleanup utility for NI Flag Classification
Clears previous training artifacts and cached models
"""

import os
import shutil
from pathlib import Path
import argparse
from datetime import datetime

def cleanup_training_artifacts(output_dir="output", experiments_dir="experiments", 
                              backup=True, verbose=True):
    """
    Clean up training artifacts with optional backup
    
    Args:
        output_dir: Main output directory with logs
        experiments_dir: Experiments directory
        backup: Whether to backup before deletion
        verbose: Print detailed information
    """
    
    cleaned_items = []
    backup_dir = None
    
    # Create backup if requested
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"backups/training_backup_{timestamp}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        if verbose:
            print(f"📦 Creating backup in: {backup_dir}")
    
    # Clean output directory
    output_path = Path(output_dir)
    if output_path.exists():
        # Backup logs if requested
        if backup:
            log_files = list(output_path.glob("log.txt*"))
            if log_files:
                backup_logs = backup_dir / "logs"
                backup_logs.mkdir(exist_ok=True)
                for log_file in log_files:
                    shutil.copy2(log_file, backup_logs)
                    if verbose:
                        print(f"  ↳ Backed up: {log_file.name}")
        
        # Clean logs
        for log_file in output_path.glob("log.txt*"):
            log_file.unlink()
            cleaned_items.append(f"Log: {log_file.name}")
        
        # Clean model checkpoints
        model_dirs = ["prompt_learner", "tensorboard"]
        for model_dir in model_dirs:
            model_path = output_path / model_dir
            if model_path.exists():
                if backup:
                    shutil.copytree(model_path, backup_dir / model_dir)
                shutil.rmtree(model_path)
                cleaned_items.append(f"Directory: {model_dir}")
    
    # Clean experiments directory
    exp_path = Path(experiments_dir)
    if exp_path.exists():
        # Backup experiments if requested
        if backup and any(exp_path.iterdir()):
            shutil.copytree(exp_path, backup_dir / "experiments")
            if verbose:
                print(f"  ↳ Backed up experiments directory")
        
        # Clean experiment subdirectories
        for exp_dir in exp_path.iterdir():
            if exp_dir.is_dir():
                shutil.rmtree(exp_dir)
                cleaned_items.append(f"Experiment: {exp_dir.name}")
    
    # Clear Python cache
    cache_dirs = ["__pycache__", ".pytest_cache"]
    for cache_dir in cache_dirs:
        for path in Path(".").rglob(cache_dir):
            shutil.rmtree(path)
            cleaned_items.append(f"Cache: {path}")
    
    # Clear .pyc files
    for pyc_file in Path(".").rglob("*.pyc"):
        pyc_file.unlink()
        cleaned_items.append(f"Compiled: {pyc_file.name}")
    
    if verbose:
        print("\n" + "="*60)
        print("🧹 CLEANUP SUMMARY")
        print("="*60)
        print(f"✅ Cleaned {len(cleaned_items)} items")
        if backup_dir:
            print(f"📦 Backup saved to: {backup_dir}")
        
        if cleaned_items[:10]:  # Show first 10 items
            print("\n📋 Cleaned items (first 10):")
            for item in cleaned_items[:10]:
                print(f"   - {item}")
            if len(cleaned_items) > 10:
                print(f"   ... and {len(cleaned_items) - 10} more items")
    
    return cleaned_items, backup_dir


def clear_gpu_cache():
    """Clear GPU memory cache"""
    import torch
    
    if torch.backends.mps.is_available():
        # For MPS (Apple Silicon)
        torch.mps.empty_cache()
        torch.mps.synchronize()
        print("✅ MPS cache cleared")
    elif torch.cuda.is_available():
        # For CUDA
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        print("✅ CUDA cache cleared")
    else:
        print("ℹ️  No GPU cache to clear (CPU mode)")


def get_training_status():
    """Check current training status"""
    output_path = Path("output")
    experiments_path = Path("experiments")
    
    print("\n" + "="*60)
    print("📊 CURRENT TRAINING STATUS")
    print("="*60)
    
    # Check for existing logs
    if output_path.exists():
        log_files = list(output_path.glob("log.txt*"))
        print(f"📝 Log files: {len(log_files)}")
        if log_files:
            most_recent = max(log_files, key=lambda x: x.stat().st_mtime)
            print(f"   Most recent: {most_recent.name}")
            print(f"   Modified: {datetime.fromtimestamp(most_recent.stat().st_mtime)}")
    
    # Check for model checkpoints
    checkpoint_path = output_path / "prompt_learner"
    if checkpoint_path.exists():
        checkpoints = list(checkpoint_path.glob("*.pth.tar*"))
        print(f"💾 Checkpoints: {len(checkpoints)}")
        if checkpoints:
            for ckpt in checkpoints[:3]:  # Show first 3
                size_mb = ckpt.stat().st_size / (1024 * 1024)
                print(f"   - {ckpt.name} ({size_mb:.1f} MB)")
    
    # Check experiments
    if experiments_path.exists():
        exp_dirs = [d for d in experiments_path.iterdir() if d.is_dir()]
        print(f"🔬 Experiments: {len(exp_dirs)}")
        for exp_dir in exp_dirs[:5]:  # Show first 5
            print(f"   - {exp_dir.name}")
    
    # Check memory usage
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024 * 1024)
    print(f"\n💾 Current memory usage: {memory_mb:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description='Clean training artifacts')
    parser.add_argument('--no-backup', action='store_true', 
                       help='Skip backup (delete permanently)')
    parser.add_argument('--quiet', action='store_true',
                       help='Minimal output')
    parser.add_argument('--status', action='store_true',
                       help='Check training status only')
    parser.add_argument('--output-dir', default='output',
                       help='Output directory to clean')
    parser.add_argument('--experiments-dir', default='experiments',
                       help='Experiments directory to clean')
    
    args = parser.parse_args()
    
    if args.status:
        get_training_status()
        return
    
    print("\n" + "="*60)
    print("🧹 TRAINING CLEANUP UTILITY")
    print("="*60)
    
    # Confirm if no backup
    if args.no_backup:
        response = input("⚠️  Delete without backup? (yes/N): ")
        if response.lower() != 'yes':
            print("❌ Cancelled")
            return
    
    # Run cleanup
    cleaned, backup_dir = cleanup_training_artifacts(
        output_dir=args.output_dir,
        experiments_dir=args.experiments_dir,
        backup=not args.no_backup,
        verbose=not args.quiet
    )
    
    # Clear GPU cache
    try:
        clear_gpu_cache()
    except Exception as e:
        print(f"⚠️  Could not clear GPU cache: {e}")
    
    print("\n✅ Cleanup complete! Ready for fresh training run.")
    
    # Show next steps
    if not args.quiet:
        print("\n📝 Next steps:")
        print("1. Start fresh training:")
        print("   python train_minimal_mps.py --trainer CoCoOp \\")
        print("     --config-file configs/trainers/CoCoOp/rn50.yaml \\")
        print("     --dataset-config-file configs/datasets/niflags.yaml \\")
        print("     --output-dir experiments/focal_fresh")


if __name__ == "__main__":
    main()
