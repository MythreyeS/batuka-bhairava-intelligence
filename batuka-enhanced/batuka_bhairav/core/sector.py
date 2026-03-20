# batuka_bhairav/core/sector.py
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple
import numpy as np


def compute_sector_strength(rows: List[dict]) -> Tuple[dict, list]:
    """
    Returns:
      sector_rank: dict sector -> normalized strength in [-0.5..+0.5] approx (then mapped to 0..1 later)
      sector_table: list of sector summary rows
    """
    sector_changes = defaultdict(list)
    sector_adv = defaultdict(int)
    sector_tot = defaultdict(int)

    for r in rows:
        sec = r.get("sector") or "UNKNOWN"
        ch = r.get("day_change_pct", 0.0)
        sector_changes[sec].append(ch)
        sector_tot[sec] += 1
        if ch > 0:
            sector_adv[sec] += 1

    sector_table = []
    for sec, changes in sector_changes.items():
        avg = float(np.mean(changes)) if changes else 0.0
        adv = sector_adv[sec]
        tot = sector_tot[sec]
        breadth = (adv / tot) if tot else 0.0
        sector_table.append({
            "sector": sec,
            "avg_change_pct": round(avg, 2),
            "breadth": round(breadth, 2),
            "count": tot
        })

    # normalize avg change to around [-0.5..+0.5] range
    if sector_table:
        avgs = [s["avg_change_pct"] for s in sector_table]
        mx = max(abs(min(avgs)), abs(max(avgs))) or 1.0
    else:
        mx = 1.0

    sector_rank = {}
    for s in sector_table:
        sector_rank[s["sector"]] = float(max(-0.5, min(0.5, (s["avg_change_pct"] / mx) * 0.5)))

    # sort best to worst
    sector_table.sort(key=lambda x: x["avg_change_pct"], reverse=True)

    return sector_rank, sector_table
