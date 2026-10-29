# -*- coding: utf-8 -*-
"""ITCH 5.0 message builders — encode synthetic messages for tests.

Each builder takes semantic fields and returns exact-length binary bytes.
These are the inverse of parser.py and pin the byte layout from both sides:
if parser and builder ever disagree, tests fail.
"""
import struct

from . import spec


def header(mtype: str, ts_ns: int = 0, stock_locate: int = 0,
           tracking: int = 0) -> bytes:
    return (mtype.encode("ascii")
            + struct.pack(">HH", stock_locate, tracking)
            + ts_ns.to_bytes(6, "big"))


def pad_stock(stock: str) -> bytes:
    assert len(stock) <= 8
    return stock.ljust(8).encode("ascii")


def system_event(code: str = "O", ts_ns: int = 0) -> bytes:
    return header("S", ts_ns) + code.encode("ascii")


def add_order(ref: int, side: str, shares: int, stock: str, price: int,
              ts_ns: int = 0, mpid: str = "") -> bytes:
    body = (struct.pack(">Q", ref) + side.encode("ascii")
            + struct.pack(">I", shares) + pad_stock(stock)
            + struct.pack(">I", price))
    if mpid:
        return header("F", ts_ns) + body + mpid.ljust(4).encode("ascii")
    return header("A", ts_ns) + body


def order_executed(ref: int, exec_shares: int, match: int,
                   ts_ns: int = 0) -> bytes:
    return header("E", ts_ns) + struct.pack(">QIQ", ref, exec_shares, match)


def order_executed_price(ref: int, exec_shares: int, match: int,
                         printable: str, exec_price: int,
                         ts_ns: int = 0) -> bytes:
    return (header("C", ts_ns) + struct.pack(">QIQ", ref, exec_shares, match)
            + printable.encode("ascii") + struct.pack(">I", exec_price))


def order_cancel(ref: int, cancel_shares: int, ts_ns: int = 0) -> bytes:
    return header("X", ts_ns) + struct.pack(">QI", ref, cancel_shares)


def order_delete(ref: int, ts_ns: int = 0) -> bytes:
    return header("D", ts_ns) + struct.pack(">Q", ref)


def order_replace(orig_ref: int, new_ref: int, new_shares: int, new_price: int,
                  ts_ns: int = 0) -> bytes:
    return (header("U", ts_ns)
            + struct.pack(">QQII", orig_ref, new_ref, new_shares, new_price))


def trade_non_cross(ref: int, side: str, shares: int, stock: str, price: int,
                    match: int, ts_ns: int = 0) -> bytes:
    return (header("P", ts_ns) + struct.pack(">Q", ref)
            + side.encode("ascii") + struct.pack(">I", shares)
            + pad_stock(stock) + struct.pack(">I", price)
            + struct.pack(">Q", match))


def cross_trade(shares: int, stock: str, cross_price: int, match: int,
                cross_type: str = "O", ts_ns: int = 0) -> bytes:
    return (header("Q", ts_ns) + struct.pack(">Q", shares) + pad_stock(stock)
            + struct.pack(">I", cross_price) + struct.pack(">Q", match)
            + cross_type.encode("ascii"))


def broken_trade(match: int, ts_ns: int = 0) -> bytes:
    return header("B", ts_ns) + struct.pack(">Q", match)


# every builder must produce exactly the spec length
assert len(system_event()) == spec.LENGTHS["S"]
assert len(add_order(1, "B", 100, "AAPL", 301500)) == spec.LENGTHS["A"]
assert len(add_order(1, "B", 100, "AAPL", 301500, mpid="MPID")) == spec.LENGTHS["F"]
assert len(order_executed(1, 10, 1)) == spec.LENGTHS["E"]
assert len(order_executed_price(1, 10, 1, "Y", 301500)) == spec.LENGTHS["C"]
assert len(order_cancel(1, 10)) == spec.LENGTHS["X"]
assert len(order_delete(1)) == spec.LENGTHS["D"]
assert len(order_replace(1, 2, 10, 301500)) == spec.LENGTHS["U"]
assert len(trade_non_cross(1, "B", 10, "AAPL", 301500, 1)) == spec.LENGTHS["P"]
assert len(cross_trade(1000, "AAPL", 301500, 1)) == spec.LENGTHS["Q"]
assert len(broken_trade(1)) == spec.LENGTHS["B"]
