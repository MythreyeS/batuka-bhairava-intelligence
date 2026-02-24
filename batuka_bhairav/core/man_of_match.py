# batuka_bhairav/core/man_of_match.py
from __future__ import annotations

from typing import List, Dict
from batuka_bhairav.config import MOM_MIN_ABS_PCT_MOVE, MOM_MIN_VOL_RATIO


def pick_man_of_match(rows: List[Dict]) -> List[Dict]:
    """
    rows: list of {symbol, sector, open, close, prev_close, day_change_pct, vol_ratio, ...}
    returns all stocks that are "meaningful movers"
    """
    mom = []
    for r in rows:
        if abs(r.get("day_change_pct", 0.0)) >= MOM_MIN_ABS_PCT_MOVE:
            mom.append(r)
            continue
        if r.get("vol_ratio", 1.0) >= MOM_MIN_VOL_RATIO:
            mom.append(r)
            continue

    # Sort by impact: abs change then volume ratio
    mom.sort(key=lambda x: (abs(x.get("day_change_pct", 0.0)), x.get("vol_ratio", 1.0)), reverse=True)
    return mom
