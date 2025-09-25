import numpy as np
from typing import Dict

def hhi(shares: np.ndarray) -> float:
    shares = np.asarray(shares, dtype=float)
    if shares.sum() <= 0:
        return 0.0
    s = shares / shares.sum()
    return float(np.sum(s ** 2))

def neff(shares: np.ndarray) -> float:
    val = hhi(shares)
    return float(1.0 / val) if val > 0 else 0.0

def hhi_weighted(shares: np.ndarray, weights: np.ndarray) -> float:
    shares = np.asarray(shares, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if shares.sum() <= 0 or weights.sum() <= 0:
        return 0.0
    sw = shares * weights
    if sw.sum() <= 0:
        return 0.0
    s = sw / sw.sum()
    return float(np.sum(s ** 2))

def neff_attention(per_type_onmask: Dict[str, float]) -> float:
    vals = np.array(list(per_type_onmask.values()), dtype=float)
    if vals.sum() <= 0:
        return 0.0
    s = vals / vals.sum()
    hh = float(np.sum(s ** 2))
    return float(1.0 / hh) if hh > 0 else 0.0
