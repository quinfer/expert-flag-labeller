from typing import List

def get_seeds(cfg) -> List[int]:
    seeds = cfg.get('seeds', [0])
    return list(seeds)
