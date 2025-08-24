#!/usr/bin/env python3
"""
Quick comparison script: Focal Loss vs Weighted CE vs Standard CE
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import subprocess
import time
from datetime import datetime

def run_experiment(name, loss_type, alpha=None, gamma=None, epochs=30):
    """Run a single experiment"""
    
    print("\n" + "="*60)
    print(f"🔬 EXPERIMENT: {name}")
    print("="*60)
    print(f"Loss Type: {loss_type}")
    if alpha is not None:
        print(f"Alpha: {alpha}, Gamma: {gamma}")
    print(f"Epochs: {epochs}")
    print("="*60)
    
    # Build command
    output_dir = f"experiments/{name}_{datetime.now().strftime('%H%M')}"
    
    cmd = [
        "python", "train_minimal_mps.py",
        "--clean",
        "--trainer", "CoCoOp",
        "--config-file", "configs/trainers/CoCoOp/rn50.yaml",
        "--dataset-config-file", "configs/datasets/niflags.yaml",
        "--output-dir", output_dir,
        "TRAINER.COCOOP.PREC", "fp32",
        "DATALOADER.NUM_WORKERS", "0",
        "OPTIM.MAX_EPOCH", str(epochs),
        "TEST.FINAL_MODEL", "best_val"
    ]
    
    # Add loss-specific parameters
    if loss_type == "focal":
        cmd.extend(["LOSS.USE_FOCAL", "True"])
        if alpha is not None:
            cmd.extend(["LOSS.ALPHA", str(alpha)])
            cmd.extend(["LOSS.GAMMA", str(gamma)])
    elif loss_type == "weighted":
        cmd.extend(["LOSS.USE_FOCAL", "False"])
        cmd.extend(["LOSS.USE_WEIGHTS", "True"])
    else:  # standard
        cmd.extend(["LOSS.USE_FOCAL", "False"])
        cmd.extend(["LOSS.USE_WEIGHTS", "False"])
    
    print(f"\n📂 Output directory: {output_dir}")
    print("🚀 Starting training...\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse results from output
        lines = result.stdout.split('\n')
        test_acc = None
        val_acc = None
        
        for i, line in enumerate(lines):
            if "test" in line.lower() and "accuracy:" in line:
                # Look for test accuracy
                for j in range(i, min(i+10, len(lines))):
                    if "accuracy:" in lines[j]:
                        parts = lines[j].split()
                        for k, part in enumerate(parts):
                            if part == "accuracy:":
                                test_acc = parts[k+1].strip('%')
                                break
                        break
            
            if "val" in line.lower() and "accuracy:" in line:
                # Look for validation accuracy
                for j in range(i, min(i+10, len(lines))):
                    if "accuracy:" in lines[j]:
                        parts = lines[j].split()
                        for k, part in enumerate(parts):
                            if part == "accuracy:":
                                val_acc = parts[k+1].strip('%')
                                break
                        break
        
        elapsed = time.time() - start_time
        
        print(f"\n✅ Experiment completed in {elapsed/60:.1f} minutes")
        print(f"📊 Results:")
        print(f"   Validation Accuracy: {val_acc}%")
        print(f"   Test Accuracy: {test_acc}%")
        
        return {
            'name': name,
            'loss_type': loss_type,
            'alpha': alpha,
            'gamma': gamma,
            'val_acc': val_acc,
            'test_acc': test_acc,
            'time_min': elapsed/60,
            'output_dir': output_dir
        }
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Experiment failed: {e}")
        return None


def main():
    print("\n" + "="*60)
    print("🔬 FOCAL LOSS OPTIMIZATION EXPERIMENTS")
    print("="*60)
    print("Running experiments to find optimal loss configuration")
    
    experiments = [
        # Baseline
        ("baseline_ce", "standard", None, None, 20),
        
        # Weighted CE (simpler alternative)
        ("weighted_ce", "weighted", None, None, 20),
        
        # Focal loss variants (gentler)
        ("focal_gentle", "focal", 0.5, 1.0, 20),  # Less aggressive
        ("focal_very_gentle", "focal", 0.75, 0.5, 20),  # Even gentler
        
        # If those work, try slightly more aggressive
        ("focal_medium", "focal", 0.5, 1.5, 20),
    ]
    
    results = []
    
    print(f"\n📋 Planned experiments: {len(experiments)}")
    for exp in experiments:
        print(f"   - {exp[0]}")
    
    response = input("\n🚀 Run all experiments? (y/n): ")
    if response.lower() != 'y':
        print("Select which to run:")
        for i, exp in enumerate(experiments):
            print(f"{i+1}. {exp[0]}")
        
        selection = input("Enter numbers (comma-separated) or 'all': ")
        if selection.lower() != 'all':
            indices = [int(x.strip())-1 for x in selection.split(',')]
            experiments = [experiments[i] for i in indices]
    
    print(f"\n🏃 Running {len(experiments)} experiments...")
    
    for exp in experiments:
        result = run_experiment(*exp)
        if result:
            results.append(result)
    
    # Summary
    if results:
        print("\n" + "="*60)
        print("📊 EXPERIMENT SUMMARY")
        print("="*60)
        
        print("\n| Experiment | Loss Type | α | γ | Val Acc | Test Acc | Time |")
        print("|------------|-----------|---|---|---------|----------|------|")
        
        for r in results:
            alpha_str = f"{r['alpha']:.2f}" if r['alpha'] else "-"
            gamma_str = f"{r['gamma']:.1f}" if r['gamma'] else "-"
            print(f"| {r['name'][:12]:12} | {r['loss_type']:9} | {alpha_str:3} | {gamma_str:3} | {r['val_acc']:7}% | {r['test_acc']:8}% | {r['time_min']:4.1f}m |")
        
        # Find best
        best = max(results, key=lambda x: float(x['test_acc']) if x['test_acc'] else 0)
        print(f"\n🏆 Best result: {best['name']} with {best['test_acc']}% test accuracy")
        print(f"   Output: {best['output_dir']}")


if __name__ == "__main__":
    main()
