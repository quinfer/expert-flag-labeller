#!/bin/bash
# Run ablation with nohup - output goes to nohup.out
nohup ./run_ablation_persistent.sh > ablation_study_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Get the process ID
PID=$!
echo "🚀 Ablation study started with PID: $PID"
echo "📝 Log file: ablation_study_$(date +%Y%m%d_%H%M%S).log"
echo "📊 Monitor progress with: tail -f ablation_study_*.log"
echo "🔍 Check if running: ps aux | grep $PID"
