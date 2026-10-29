# -*- coding: utf-8 -*-
"""Shadow order book built from ITCH order-flow messages.

The Python golden model for the 0.2.x FPGA order book kernel: consume the
A/F/E/C/X/D/U stream, maintain live orders + aggregated price levels, and
answer top-of-book queries. Deliberately simple (dict-of-dict) — speed is
the FPGA's job, correctness is this model's job.
"""
from .parser import iter_messages


class ShadowBook:
    def __init__(self):
        # order_ref -> {side, shares, stock, price}
        self.orders = {}
        # (stock, side) -> {price -> total_shares}
        self.levels = {}
        self.msg_count = 0

    # ---- stream in ----
    def apply(self, msg: dict) -> None:
        t = msg["type"]
        self.msg_count += 1
        if t in ("A", "F"):
            self._add(msg["order_ref"], msg["side"], msg["shares"],
                      msg["stock"], msg["price"])
        elif t == "U":
            o = self.orders.pop(msg["orig_ref"], None)
            if o is not None:
                self._level(o["stock"], o["side"], o["price"], -o["shares"])
            self._add(msg["new_ref"], o["side"] if o else "?",
                      msg["new_shares"],
                      o["stock"] if o else "?", msg["new_price"])
        elif t in ("E", "C"):
            self._reduce(msg["order_ref"],
                         msg.get("exec_shares", msg.get("cancel_shares", 0)))
        elif t == "X":
            self._reduce(msg["order_ref"], msg["cancel_shares"])
        elif t == "D":
            o = self.orders.pop(msg["order_ref"], None)
            if o is not None:
                self._level(o["stock"], o["side"], o["price"], -o["shares"])
        # S/P/Q/B/H: no effect on the book

    def apply_stream(self, buf: bytes) -> int:
        n = 0
        for msg in iter_messages(buf):
            self.apply(msg)
            n += 1
        return n

    # ---- internals ----
    def _add(self, ref, side, shares, stock, price):
        self.orders[ref] = {"side": side, "shares": shares,
                            "stock": stock, "price": price}
        self._level(stock, side, price, shares)

    def _reduce(self, ref, shares):
        o = self.orders.get(ref)
        if o is None or shares <= 0:
            return
        take = min(shares, o["shares"])
        o["shares"] -= take
        self._level(o["stock"], o["side"], o["price"], -take)
        if o["shares"] == 0:
            del self.orders[ref]

    def _level(self, stock, side, price, delta):
        lv = self.levels.setdefault((stock, side), {})
        cur = lv.get(price, 0) + delta
        if cur > 0:
            lv[price] = cur
        else:
            lv.pop(price, None)

    # ---- queries ----
    def bbo(self, stock: str):
        """Return (best_bid, best_ask) as (price, shares) or None tuples."""
        bid = self.levels.get((stock, "B"), {})
        ask = self.levels.get((stock, "S"), {})
        bb = max(bid.items()) if bid else None
        ba = min(ask.items()) if ask else None
        return bb, ba

    def spread(self, stock: str):
        bb, ba = self.bbo(stock)
        if bb and ba:
            return ba[0] - bb[0]
        return None
