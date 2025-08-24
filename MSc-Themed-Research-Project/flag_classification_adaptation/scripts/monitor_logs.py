#!/usr/bin/env python3
"""
Find and monitor active training logs
"""

import os
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def find_training_logs():
    """Find all training log files"""
    logs = []
    
    # Check default output directory
    adaptation_dir = Path(__file__).resolve().parent
    output_log = adaptation_dir / "output" / "log.txt"
    if output_log.exists():
        logs.append(output_log)
    
    # Check experiments directory
    exp_dir = adaptation_dir / "experiments"
    if exp_dir.exists():
        for exp_subdir in exp_dir.iterdir():
            if exp_subdir.is_dir():
                log_file = exp_subdir / "log.txt"
                if log_file.exists():
                    logs.append(log_file)
    
    return logs

def get_log_info(log_path):
    """Get information about a log file"""
    stat = log_path.stat()
    mod_time = datetime.fromtimestamp(stat.st_mtime)
    size_kb = stat.st_size / 1024
    
    # Check if recently modified (within 5 minutes)
    is_active = (datetime.now() - mod_time) < timedelta(minutes=5)
    
    # Try to get last few lines
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
            last_lines = lines[-3:] if len(lines) >= 3 else lines
            
            # Check for epoch/iteration info
            training_info = None
            for line in reversed(lines[-20:]):
                if 'epoch' in line.lower() or 'iter' in line.lower():
                    training_info = line.strip()
                    break
    except:
        last_lines = []
        training_info = None
    
    return {
        'path': log_path,
        'modified': mod_time,
        'size_kb': size_kb,
        'is_active': is_active,
        'last_lines': last_lines,
        'training_info': training_info
    }

def main():
    print("\n" + "="*60)
    print("🔍 TRAINING LOG MONITOR")
    print("="*60)
    
    # Find all logs
    logs = find_training_logs()
    
    if not logs:
        print("\n❌ No training logs found!")
        print("\nMake sure training is running:")
        print("  python train_minimal_mps.py --trainer CoCoOp \\")
        print("    --config-file configs/trainers/CoCoOp/rn50.yaml \\")
        print("    --dataset-config-file configs/datasets/niflags.yaml \\")
        print("    --output-dir experiments/YOUR_NAME")
        return
    
    # Get info for each log
    log_infos = [get_log_info(log) for log in logs]
    
    # Sort by modification time
    log_infos.sort(key=lambda x: x['modified'], reverse=True)
    
    print(f"\n📄 Found {len(logs)} log file(s):")
    print("-" * 60)
    
    active_log = None
    for info in log_infos:
        status = "🟢 ACTIVE" if info['is_active'] else "⚪ IDLE"
        print(f"\n{status} {info['path']}")
        print(f"  Modified: {info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Size: {info['size_kb']:.1f} KB")
        
        if info['training_info']:
            print(f"  Status: {info['training_info'][:60]}...")
        
        if info['is_active'] and not active_log:
            active_log = info
    
    # Monitor the active log
    if active_log:
        print("\n" + "="*60)
        print(f"📺 MONITORING: {active_log['path']}")
        print("="*60)
        print("Press Ctrl+C to stop\n")
        
        try:
            # Use tail -f to monitor
            subprocess.run(['tail', '-f', str(active_log['path'])])
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped")
    else:
        # Show how to monitor the most recent
        most_recent = log_infos[0]
        print("\n" + "="*60)
        print("💡 No active training detected")
        print("="*60)
        print(f"\nMost recent log: {most_recent['path']}")
        print(f"Last modified: {most_recent['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📺 To monitor this log, run:")
        print(f"  tail -f {most_recent['path']}")
        
        print("\n🚀 To start new training with focal loss:")
        print("  python train_minimal_mps.py --clean --trainer CoCoOp \\")
        print("    --config-file configs/trainers/CoCoOp/rn50.yaml \\")
        print("    --dataset-config-file configs/datasets/niflags.yaml \\")
        print("    --output-dir experiments/focal_week9 \\")
        print("    TRAINER.COCOOP.PREC fp32 \\")
        print("    DATALOADER.NUM_WORKERS 0 \\")
        print("    OPTIM.MAX_EPOCH 50")

if __name__ == "__main__":
    main()
