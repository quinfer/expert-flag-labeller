#!/usr/bin/env python3
"""
Comprehensive Comparison Script for Flag Classification Approaches
Tests different consolidation levels and class balancing strategies
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add current directory to path
sys.path.append('.')


class FlagClassificationComparison:
    """Comprehensive comparison of different training approaches"""
    
    def __init__(self, base_output_dir="experiments/comparison_study"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        self.results = []
        
        # Define test configurations
        self.test_configs = self._create_test_configurations()
        
        print(f"🔬 Flag Classification Comparison Study")
        print(f"   Output directory: {self.base_output_dir}")
        print(f"   Test configurations: {len(self.test_configs)}")
    
    def _create_test_configurations(self):
        """Create comprehensive test configurations"""
        configs = []
        
        # 16-class consolidated tests
        configs.extend([
            {
                'name': '16class_uniform_nofocal',
                'dataset': 'NIFlagsConsolidatedDynamic',
                'class_balance_method': 'uniform',
                'use_focal_loss': False,
                'epochs': 50,
                'description': '16-class baseline with uniform weights'
            },
            {
                'name': '16class_balanced_nofocal',
                'dataset': 'NIFlagsConsolidatedDynamic',
                'class_balance_method': 'inverse_frequency',
                'use_focal_loss': False,
                'epochs': 50,
                'description': '16-class with inverse frequency weights'
            },
            {
                'name': '16class_uniform_focal',
                'dataset': 'NIFlagsConsolidatedDynamic',
                'class_balance_method': 'uniform',
                'use_focal_loss': True,
                'focal_alpha': 0.5,
                'focal_gamma': 1.0,
                'epochs': 50,
                'description': '16-class with focal loss'
            },
            {
                'name': '16class_balanced_focal',
                'dataset': 'NIFlagsConsolidatedDynamic',
                'class_balance_method': 'inverse_frequency',
                'use_focal_loss': True,
                'focal_alpha': 0.5,
                'focal_gamma': 1.0,
                'epochs': 50,
                'description': '16-class with balanced weights + focal loss'
            },
        ])
        
        # 7-class super-consolidated tests
        configs.extend([
            {
                'name': '7class_uniform_nofocal',
                'dataset': 'NIFlagsSuperConsolidatedDynamic',
                'class_balance_method': 'uniform',
                'use_focal_loss': False,
                'epochs': 75,  # More epochs for harder problem
                'description': '7-class baseline with uniform weights'
            },
            {
                'name': '7class_balanced_focal_aggressive',
                'dataset': 'NIFlagsSuperConsolidatedDynamic',
                'class_balance_method': 'sqrt_inverse',  # Less aggressive for extreme imbalance
                'use_focal_loss': True,
                'focal_alpha': 0.3,
                'focal_gamma': 2.0,  # Higher gamma for extreme imbalance
                'epochs': 100,
                'description': '7-class with aggressive focal loss for extreme imbalance'
            },
        ])
        
        return configs
    
    def run_single_experiment(self, config):
        """Run a single training experiment"""
        print(f"\n{'='*60}")
        print(f"🧪 Running: {config['name']}")
        print(f"   {config['description']}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Create output directory for this experiment
        exp_dir = self.base_output_dir / config['name']
        exp_dir.mkdir(exist_ok=True)
        
        # Build command
        cmd = [
            'python', 'train_dynamic.py',
            '--config-file', 'configs/trainers/CoCoOp/vit_b32.yaml',
            '--output-dir', str(exp_dir),
            '--class-balance-method', config['class_balance_method'],
            '--clean',
            'DATASET.NAME', config['dataset'],
            'OPTIM.MAX_EPOCH', str(config['epochs']),
            'TRAINER.COCOOP.PREC', 'fp32',
            'DATALOADER.NUM_WORKERS', '0',
        ]
        
        # Add focal loss parameters if enabled
        if config['use_focal_loss']:
            cmd.append('--use-focal-loss')
            if 'focal_alpha' in config:
                cmd.extend(['--focal-alpha', str(config['focal_alpha'])])
            if 'focal_gamma' in config:
                cmd.extend(['--focal-gamma', str(config['focal_gamma'])])
        
        # Run training
        try:
            print(f"🚀 Command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if result.returncode == 0:
                print(f"✅ Training completed successfully")
                success = True
                error_msg = None
            else:
                print(f"❌ Training failed with return code {result.returncode}")
                print(f"Error output: {result.stderr[-500:]}")  # Last 500 chars
                success = False
                error_msg = result.stderr[-500:]
        
        except subprocess.TimeoutExpired:
            print(f"⏰ Training timed out after 30 minutes")
            success = False
            error_msg = "Timeout after 30 minutes"
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            success = False
            error_msg = str(e)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Parse results if successful
        results = self._parse_results(exp_dir) if success else {}
        
        # Store experiment results
        experiment_result = {
            'name': config['name'],
            'description': config['description'],
            'dataset': config['dataset'],
            'class_balance_method': config['class_balance_method'],
            'use_focal_loss': config['use_focal_loss'],
            'epochs': config['epochs'],
            'success': success,
            'duration_minutes': duration / 60,
            'error_msg': error_msg,
            'timestamp': datetime.now().isoformat(),
            **results  # Add parsed metrics
        }
        
        # Add focal loss parameters if used
        if config['use_focal_loss']:
            experiment_result['focal_alpha'] = config.get('focal_alpha', 0.5)
            experiment_result['focal_gamma'] = config.get('focal_gamma', 1.0)
        
        self.results.append(experiment_result)
        
        # Save intermediate results
        self._save_results()
        
        return experiment_result
    
    def _parse_results(self, exp_dir):
        """Parse training results from experiment directory"""
        results = {}
        
        try:
            # Look for log files
            log_files = list(exp_dir.glob("log.txt*"))
            if log_files:
                log_file = log_files[0]  # Use the first/most recent log
                results.update(self._parse_log_file(log_file))
            
            # Look for other result files
            # Add more parsing as needed
            
        except Exception as e:
            print(f"⚠️ Error parsing results from {exp_dir}: {e}")
        
        return results
    
    def _parse_log_file(self, log_file):
        """Parse metrics from training log file"""
        results = {}
        
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Extract final test results
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "=> result" in line:
                    # Parse the results section
                    try:
                        # Look for accuracy
                        for j in range(i, min(i+10, len(lines))):
                            if "accuracy:" in lines[j]:
                                acc_str = lines[j].split("accuracy:")[1].split("%")[0].strip()
                                results['accuracy'] = float(acc_str)
                            elif "macro_f1:" in lines[j]:
                                f1_str = lines[j].split("macro_f1:")[1].split("%")[0].strip()
                                results['macro_f1'] = float(f1_str)
                            elif "total:" in lines[j]:
                                total_str = lines[j].split("total:")[1].strip()
                                results['total_samples'] = int(total_str)
                            elif "correct:" in lines[j]:
                                correct_str = lines[j].split("correct:")[1].strip()
                                results['correct_samples'] = int(correct_str)
                    except (ValueError, IndexError) as e:
                        print(f"⚠️ Error parsing result line: {line}, error: {e}")
            
            # Extract training time
            if "Training completed in" in content:
                time_match = content.split("Training completed in")[1].split("minutes")[0].strip()
                try:
                    results['training_time_minutes'] = float(time_match)
                except ValueError:
                    pass
            
        except Exception as e:
            print(f"⚠️ Error parsing log file {log_file}: {e}")
        
        return results
    
    def run_all_experiments(self):
        """Run all configured experiments"""
        print(f"\n🚀 Starting comprehensive comparison study")
        print(f"   Total experiments: {len(self.test_configs)}")
        print(f"   Estimated time: {sum(c.get('epochs', 50) for c in self.test_configs) * 2} minutes")
        
        for i, config in enumerate(self.test_configs):
            print(f"\n📊 Progress: {i+1}/{len(self.test_configs)}")
            self.run_single_experiment(config)
        
        print(f"\n✅ All experiments completed!")
        self._generate_final_report()
    
    def _save_results(self):
        """Save current results to JSON file"""
        results_file = self.base_output_dir / "comparison_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def _generate_final_report(self):
        """Generate comprehensive final report"""
        print(f"\n📊 Generating final comparison report...")
        
        # Create DataFrame for analysis
        df = pd.DataFrame(self.results)
        
        # Save detailed CSV
        csv_file = self.base_output_dir / "detailed_results.csv"
        df.to_csv(csv_file, index=False)
        
        # Generate summary report
        self._create_summary_report(df)
        
        print(f"📁 Results saved to: {self.base_output_dir}")
        print(f"   📊 Detailed CSV: detailed_results.csv")
        print(f"   📋 Summary report: summary_report.md")
        print(f"   🔧 Raw JSON: comparison_results.json")
    
    def _create_summary_report(self, df):
        """Create markdown summary report"""
        report_file = self.base_output_dir / "summary_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Flag Classification Comparison Study Results\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall summary
            successful_runs = df[df['success'] == True]
            f.write(f"## Overall Summary\n\n")
            f.write(f"- Total experiments: {len(df)}\n")
            f.write(f"- Successful runs: {len(successful_runs)}\n")
            f.write(f"- Failed runs: {len(df) - len(successful_runs)}\n")
            f.write(f"- Total training time: {df['duration_minutes'].sum():.1f} minutes\n\n")
            
            if len(successful_runs) > 0:
                # Performance comparison
                f.write("## Performance Comparison\n\n")
                f.write("| Experiment | Dataset | Balance Method | Focal Loss | Accuracy | Macro F1 | Training Time |\n")
                f.write("|------------|---------|----------------|------------|----------|----------|---------------|\n")
                
                # Sort by accuracy descending
                sorted_results = successful_runs.sort_values('accuracy', ascending=False)
                
                for _, row in sorted_results.iterrows():
                    focal = "Yes" if row.get('use_focal_loss', False) else "No"
                    dataset_short = row['dataset'].replace('NIFlags', '').replace('Dynamic', '')
                    acc = f"{row.get('accuracy', 0):.1f}%" if 'accuracy' in row else "N/A"
                    f1 = f"{row.get('macro_f1', 0):.1f}%" if 'macro_f1' in row else "N/A"
                    time_str = f"{row.get('duration_minutes', 0):.1f}m"
                    
                    f.write(f"| {row['name']} | {dataset_short} | {row['class_balance_method']} | {focal} | {acc} | {f1} | {time_str} |\n")
                
                # Best results summary
                f.write("\n## Key Findings\n\n")
                best_acc = sorted_results.iloc[0]
                best_f1 = successful_runs.loc[successful_runs['macro_f1'].idxmax()] if 'macro_f1' in successful_runs.columns else None
                
                f.write(f"### Best Overall Accuracy\n")
                f.write(f"- **{best_acc['name']}**: {best_acc.get('accuracy', 0):.1f}% accuracy\n")
                f.write(f"- Configuration: {best_acc['description']}\n")
                f.write(f"- Training time: {best_acc.get('duration_minutes', 0):.1f} minutes\n\n")
                
                if best_f1 is not None and 'macro_f1' in best_f1:
                    f.write(f"### Best Macro F1 (Class Balance)\n")
                    f.write(f"- **{best_f1['name']}**: {best_f1.get('macro_f1', 0):.1f}% macro F1\n")
                    f.write(f"- Configuration: {best_f1['description']}\n\n")
                
                # Analysis by dataset
                f.write("## Analysis by Dataset\n\n")
                for dataset in df['dataset'].unique():
                    dataset_results = successful_runs[successful_runs['dataset'] == dataset]
                    if len(dataset_results) > 0:
                        best_dataset = dataset_results.loc[dataset_results['accuracy'].idxmax()]
                        dataset_short = dataset.replace('NIFlags', '').replace('Dynamic', '')
                        
                        f.write(f"### {dataset_short}\n")
                        f.write(f"- Best accuracy: **{best_dataset.get('accuracy', 0):.1f}%** ({best_dataset['name']})\n")
                        f.write(f"- Best approach: {best_dataset['class_balance_method']} weights")
                        if best_dataset.get('use_focal_loss', False):
                            f.write(f" + focal loss (α={best_dataset.get('focal_alpha', 0.5)}, γ={best_dataset.get('focal_gamma', 1.0)})")
                        f.write("\n\n")
            
            # Failed experiments
            failed_runs = df[df['success'] == False]
            if len(failed_runs) > 0:
                f.write("## Failed Experiments\n\n")
                for _, row in failed_runs.iterrows():
                    f.write(f"- **{row['name']}**: {row.get('error_msg', 'Unknown error')}\n")
        
        print(f"📋 Summary report created: {report_file}")


def main():
    """Main function to run comparison study"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Flag Classification Comparison")
    parser.add_argument("--output-dir", type=str, default="experiments/comparison_study",
                       help="Output directory for comparison results")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick comparison with fewer configurations")
    parser.add_argument("--single", type=str,
                       help="Run single experiment by name")
    
    args = parser.parse_args()
    
    # Initialize comparison
    comparison = FlagClassificationComparison(args.output_dir)
    
    if args.quick:
        # Run only essential comparisons
        comparison.test_configs = [
            config for config in comparison.test_configs 
            if 'uniform' in config['name'] or 'balanced_focal' in config['name']
        ]
        print(f"🏃 Quick mode: running {len(comparison.test_configs)} essential experiments")
    
    if args.single:
        # Run single experiment
        config = next((c for c in comparison.test_configs if c['name'] == args.single), None)
        if config:
            comparison.run_single_experiment(config)
        else:
            print(f"❌ Experiment '{args.single}' not found")
            print("Available experiments:")
            for c in comparison.test_configs:
                print(f"  - {c['name']}: {c['description']}")
        return
    
    # Run all experiments
    comparison.run_all_experiments()


if __name__ == "__main__":
    main()