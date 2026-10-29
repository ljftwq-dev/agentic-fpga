# -*- coding: utf-8 -*-
"""ITCH file stats CLI — run against a real NASDAQ TotalView sample file.

Usage:  python -m itch5.stats <path/to/sample.itch>
"""
import sys
import time
from collections import Counter

from .parser import ItchParserError, iter_messages


def main(path: str) -> int:
    t0 = time.perf_counter()
    with open(path, "rb") as f:
        buf = f.read()
    t_read = time.perf_counter() - t0

    counts = Counter()
    n_bytes = 0
    ts_min, ts_max = None, None
    t0 = time.perf_counter()
    try:
        for msg in iter_messages(buf):
            counts[msg["type"]] += 1
            n_bytes += msg["_len"]
            ts = msg["ts_ns"]
            if ts:
                ts_min = ts if ts_min is None else min(ts_min, ts)
                ts_max = ts if ts_max is None else max(ts_max, ts)
    except ItchParserError as e:
        print(f"[STOP] {e}  (parsed {n_bytes} bytes cleanly before this)")
    t_parse = time.perf_counter() - t0

    total = sum(counts.values())
    print(f"file: {path}  ({len(buf):,} bytes, read {t_read:.2f}s)")
    print(f"messages: {total:,}   parsed bytes: {n_bytes:,}   "
          f"parse: {t_parse:.2f}s  ({total / max(t_parse, 1e-9):,.0f} msg/s)")
    if ts_min is not None:
        def hms(ns):
            s = ns / 1e9
            return f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d}"
        print(f"time span: {hms(ts_min)} .. {hms(ts_max)}")
    print("\ntype  count      share")
    for t, c in counts.most_common():
        print(f"  {t}   {c:>10,}  {c / total * 100:5.1f}%")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
