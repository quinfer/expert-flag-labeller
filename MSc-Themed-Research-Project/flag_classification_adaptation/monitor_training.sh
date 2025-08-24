#!/bin/bash
# Find and monitor the most recent training log

echo "🔍 Finding active training logs..."
echo ""

# Function to check if file was modified recently (within last 5 minutes)
is_recent() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        local mod_time=$(stat -f %m "$1" 2>/dev/null)
    else
        # Linux
        local mod_time=$(stat -c %Y "$1" 2>/dev/null)
    fi
    
    if [ -z "$mod_time" ]; then
        return 1
    fi
    
    local current_time=$(date +%s)
    local diff=$((current_time - mod_time))
    
    # Check if modified within last 5 minutes (300 seconds)
    [ $diff -lt 300 ]
}

# Find all log.txt files
log_files=()
if [ -f "output/log.txt" ]; then
    log_files+=("output/log.txt")
fi

for exp_dir in experiments/*/; do
    if [ -f "${exp_dir}log.txt" ]; then
        log_files+=("${exp_dir}log.txt")
    fi
done

if [ ${#log_files[@]} -eq 0 ]; then
    echo "❌ No log files found!"
    echo ""
    echo "Make sure training is running with one of these commands:"
    echo "  python train_minimal_mps.py ... --output-dir experiments/YOUR_EXPERIMENT_NAME"
    echo "  python train_minimal_mps.py ... (uses output/log.txt by default)"
    exit 1
fi

# Find the most recently modified log
most_recent=""
most_recent_time=0

for log in "${log_files[@]}"; do
    if [[ "$OSTYPE" == "darwin"* ]]; then
        mod_time=$(stat -f %m "$log" 2>/dev/null)
    else
        mod_time=$(stat -c %Y "$log" 2>/dev/null)
    fi
    
    if [ ! -z "$mod_time" ] && [ "$mod_time" -gt "$most_recent_time" ]; then
        most_recent="$log"
        most_recent_time=$mod_time
    fi
    
    # Show all found logs
    if is_recent "$log"; then
        echo "✅ ACTIVE: $log (recently modified)"
    else
        echo "📄 Found: $log"
    fi
done

echo ""
if [ ! -z "$most_recent" ]; then
    echo "📊 Most recent log: $most_recent"
    
    # Check if it's actively being written to
    if is_recent "$most_recent"; then
        echo "✅ This log is actively being updated!"
    else
        echo "⚠️  This log hasn't been updated recently"
    fi
    
    echo ""
    echo "📺 Starting monitor (Ctrl+C to stop)..."
    echo "="*60
    echo ""
    
    # Monitor the log
    tail -f "$most_recent"
else
    echo "❌ No log files found!"
fi
