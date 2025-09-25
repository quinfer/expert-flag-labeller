import json
from pathlib import Path
from typing import List, Dict
import numpy as np
import pandas as pd


def per_type_recall(df_preds: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame[type, recall] using y_true/y_pred columns and flag_type."""
    out = []
    for t, g in df_preds.groupby('flag_type'):
        y_true = g['y_true'].to_numpy()
        y_pred = g['y_pred'].to_numpy()
        if len(y_true) == 0:
            rec = np.nan
        else:
            rec = float((y_true == y_pred).sum() / len(y_true))
        out.append({'type': t, 'recall': rec})
    return pd.DataFrame(out)


def macro_f1(df_preds: pd.DataFrame) -> float:
    """Compute macro-F1 over all classes indicated by y_true/y_pred."""
    types = sorted(set(df_preds['y_true']).union(set(df_preds['y_pred'])))
    f1s = []
    for c in types:
        tp = ((df_preds['y_true'] == c) & (df_preds['y_pred'] == c)).sum()
        fp = ((df_preds['y_true'] != c) & (df_preds['y_pred'] == c)).sum()
        fn = ((df_preds['y_true'] == c) & (df_preds['y_pred'] != c)).sum()
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        f1s.append(f1)
    return float(np.mean(f1s)) if f1s else 0.0


def aggregate_over_seeds(metric_fn, paths: List[Path]) -> Dict:
    """Compute metric over multiple seed files; returns {'mean': x, 'std': y}.
    Expects Parquet files with predictions (image_path,y_true,y_pred,flag_type).
    """
    vals = []
    for p in paths:
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        vals.append(metric_fn(df))
    if not vals:
        return {'mean': np.nan, 'std': np.nan}
    arr = np.array(vals, dtype=float)
    return {'mean': float(arr.mean()), 'std': float(arr.std(ddof=1) if len(arr) > 1 else 0.0)}
