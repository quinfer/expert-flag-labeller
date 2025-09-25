#!/usr/bin/env python3
import argparse
from pathlib import Path
import glob
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yaml

from flag_types import TYPE_ORDER
from masks import load_mask, on_mask_attention
from concentration import neff_attention, hhi, hhi_weighted
from metrics import per_type_recall, macro_f1, aggregate_over_seeds
from rs5m_attention_rollout import extract_attention_for_images, setup_device
import torch


def load_index(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if 'flag_type' not in df.columns or 'image_path' not in df.columns:
        raise ValueError('index.csv must contain image_path, flag_type columns')
    return df


def compute_onmask_by_type_real(
    df_idx: pd.DataFrame, 
    checkpoint_path: Path, 
    backbone_path: Path,
    num_classes: int,
    n_per_type: int, 
    device: torch.device
) -> tuple[dict, dict]:
    """
    Compute real on-mask attention using trained RS5M models.
    
    Args:
        df_idx: DataFrame with image paths and flag types
        checkpoint_path: Path to trained model checkpoint
        backbone_path: Path to RS5M backbone
        num_classes: Number of classes in the model
        n_per_type: Number of images per type to analyze
        device: Device to run inference on
        
    Returns:
        Tuple of (per_type_attention_values, per_type_attention_maps)
    """
    per_type_vals = {}
    per_type_heatmaps = {}
    
    for t in TYPE_ORDER:
        df_t = df_idx[df_idx['flag_type'] == t]
        if len(df_t) == 0:
            continue
        
        sample_paths = df_t['image_path'].tolist()[:n_per_type]
        print(f"🔍 Extracting attention for {t}: {len(sample_paths)} images")
        
        # Extract real RS5M attention roll-outs
        attention_maps = extract_attention_for_images(
            sample_paths, checkpoint_path, backbone_path, num_classes, device
        )
        
        vals = []
        maps = []
        
        for i, path in enumerate(sample_paths):
            if i < len(attention_maps):
                attention_map = attention_maps[i]
                
                # Load mask and compute on-mask attention
                mask = load_mask(Path(path))
                if mask is not None:
                    on_mask_val = on_mask_attention(attention_map, mask)
                    vals.append(on_mask_val)
                    maps.append(attention_map)
                else:
                    # If no mask available, use full attention mean as proxy
                    vals.append(attention_map.mean())
                    maps.append(attention_map)
        
        if vals:
            per_type_vals[t] = np.array(vals)
            per_type_heatmaps[t] = maps
            print(f"✅ {t}: {len(vals)} attention maps, mean on-mask: {np.mean(vals):.4f}")

    return per_type_vals, per_type_heatmaps


def plot_figure(per_type_vals_before, per_type_vals_after, per_type_maps_before, per_type_maps_after, vmin, vmax, out_png: Path, out_pdf: Path):
    types = [t for t in TYPE_ORDER if t in per_type_vals_after]
    cols = 3
    rows = int(np.ceil(len(types) / cols))
    fig = plt.figure(figsize=(6*cols, 4.5*rows + 3))
    gs = fig.add_gridspec(rows+1, cols, height_ratios=[1]*rows + [0.9])

    # Heatmaps (after) with fixed colorbar
    all_maps = []
    for t in types:
        for m in per_type_maps_after.get(t, [])[:1]:
            all_maps.append(m)
    # Colorbar scale
    norm_min, norm_max = vmin, vmax

    for idx, t in enumerate(types):
        r, c = divmod(idx, cols)
        ax = fig.add_subplot(gs[r, c])
        # show first map per type if available
        maps = per_type_maps_after.get(t, [])
        if maps:
            m = maps[0]
            mm = (m - m.min()) / (m.max() - m.min() + 1e-8)
            im = ax.imshow(mm, vmin=norm_min, vmax=norm_max, cmap='jet')
        ax.set_title(t, fontsize=11)
        ax.axis('off')

    # Single colorbar
    cax = fig.add_axes([0.92, 0.2, 0.015, 0.6])
    cb = plt.colorbar(plt.cm.ScalarMappable(cmap='jet'), cax=cax)
    cb.set_label('Attention Intensity (normalised)', rotation=270, labelpad=12)

    # Bar chart (bottom row)
    axb = fig.add_subplot(gs[rows, :])
    means_b = [per_type_vals_before[t].mean() if t in per_type_vals_before else np.nan for t in types]
    stds_b  = [per_type_vals_before[t].std(ddof=1) if t in per_type_vals_before and len(per_type_vals_before[t])>1 else 0.0 for t in types]
    means_a = [per_type_vals_after[t].mean() if t in per_type_vals_after else np.nan for t in types]
    stds_a  = [per_type_vals_after[t].std(ddof=1) if t in per_type_vals_after and len(per_type_vals_after[t])>1 else 0.0 for t in types]
    x = np.arange(len(types))
    w = 0.35
    axb.bar(x - w/2, means_b, w, yerr=stds_b, label='Before', alpha=0.8)
    axb.bar(x + w/2, means_a, w, yerr=stds_a, label='After', alpha=0.8)
    axb.set_xticks(x)
    axb.set_xticklabels([t.split('–')[0].strip() for t in types], rotation=0)
    axb.set_ylabel('On-mask attention share')
    axb.set_title('Per-type on-mask attention (Before vs After)')
    axb.legend()

    fig.tight_layout(rect=[0.03, 0.05, 0.9, 0.95])
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_pdf)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', type=Path, required=True)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    seeds = cfg.get('seeds', [0])
    vmin = float(cfg.get('global_vmin', 0.0))
    vmax = float(cfg.get('global_vmax', 0.95))
    n_images = int(cfg.get('n_images_per_type', 8))
    index_csv = Path(cfg['index_csv'])

    df_idx = load_index(index_csv)
    device = setup_device()
    backbone_path = Path(cfg['backbone_checkpoint']).resolve()

    # BEFORE: Extract attention from 16-class model
    before_checkpoints = cfg.get('checkpoints_before', [])
    if before_checkpoints:
        before_checkpoint = Path(before_checkpoints[0]).resolve()
        print(f"\n🔍 BEFORE: Extracting attention from 16-class model")
        per_type_vals_before, per_type_maps_before = compute_onmask_by_type_real(
            df_idx, before_checkpoint, backbone_path, 16, n_images, device
        )
    else:
        print("⚠️  No BEFORE checkpoints found")
        per_type_vals_before = {}
        per_type_maps_before = {}

    # AFTER: Extract attention from 7-class models (average across seeds)
    after_checkpoints = cfg.get('checkpoints_after', [])
    if after_checkpoints:
        print(f"\n🔍 AFTER: Extracting attention from 7-class models ({len(after_checkpoints)} seeds)")
        all_after_vals = []
        all_after_maps = []
        
        for i, checkpoint_path in enumerate(after_checkpoints):
            checkpoint = Path(checkpoint_path).resolve()
            print(f"  📊 Processing seed {i+1}/{len(after_checkpoints)}")
            vals, maps = compute_onmask_by_type_real(
                df_idx, checkpoint, backbone_path, 7, n_images, device
            )
            all_after_vals.append(vals)
            all_after_maps.append(maps)
        
        # Average attention values across seeds
        per_type_vals_after = {}
        per_type_maps_after = {}
        
        for t in TYPE_ORDER:
            type_vals = []
            type_maps = []
            
            for seed_vals, seed_maps in zip(all_after_vals, all_after_maps):
                if t in seed_vals:
                    type_vals.extend(seed_vals[t])
                if t in seed_maps:
                    type_maps.extend(seed_maps[t])
            
            if type_vals:
                per_type_vals_after[t] = np.array(type_vals)
                per_type_maps_after[t] = type_maps
        
    else:
        print("⚠️  No AFTER checkpoints found")
        per_type_vals_after = {}
        per_type_maps_after = {}

    # Concentration metrics
    shares_before = {t: per_type_vals_before[t].mean() for t in per_type_vals_before}
    shares_after  = {t: per_type_vals_after[t].mean() for t in per_type_vals_after}
    neff_b = neff_attention(shares_before)
    neff_a = neff_attention(shares_after)
    hhi_b = float(1.0 / neff_b) if neff_b > 0 else np.nan
    hhi_a = float(1.0 / neff_a) if neff_a > 0 else np.nan

    # Plot with real RS5M attention comparison
    out_png = Path('MSc-Themed-Research-Project/write-up/plots/figure1b_attention_flag_types.png')
    out_pdf = Path('MSc-Themed-Research-Project/write-up/plots/figure1b_attention_flag_types.pdf')
    plot_figure(per_type_vals_before, per_type_vals_after, per_type_maps_before, per_type_maps_after, vmin, vmax, out_png, out_pdf)

    # Predictions & metrics if available
    before_paths = [Path(p) for p in glob.glob(cfg.get('preds_before_glob', ''))]
    after_paths  = [Path(p) for p in glob.glob(cfg.get('preds_after_glob', ''))]

    if before_paths and after_paths:
        # Macro-F1 across seeds
        mf1_b = aggregate_over_seeds(macro_f1, before_paths)
        mf1_a = aggregate_over_seeds(macro_f1, after_paths)
        print(f"Macro-F1 BEFORE: {mf1_b}")
        print(f"Macro-F1 AFTER:  {mf1_a}")
        # Per-type recall for first available seed (as example)
        df_b = pd.read_parquet(before_paths[0])
        df_a = pd.read_parquet(after_paths[0])
        print('Per-type recall BEFORE:')
        print(per_type_recall(df_b))
        print('Per-type recall AFTER:')
        print(per_type_recall(df_a))

    # Print attention shares table
    print('\nOn-mask attention share (mean across images)')
    print('Type, BEFORE, AFTER, Delta')
    for t in TYPE_ORDER:
        b = shares_before.get(t, np.nan)
        a = shares_after.get(t, np.nan)
        d = a - b if np.isfinite(a) and np.isfinite(b) else np.nan
        print(f"{t},{b:.4f},{a:.4f},{d:.4f}")
    print(f"N_eff^attn BEFORE: {neff_b:.3f}  AFTER: {neff_a:.3f}")
    print(f"HHI^attn  BEFORE: {hhi_b:.3f}   AFTER: {hhi_a:.3f}")


if __name__ == '__main__':
    main()
