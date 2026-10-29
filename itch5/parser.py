# -*- coding: utf-8 -*-
"""ITCH 5.0 binary parser — the golden reference model.

Zero dependencies (stdlib only). Parses a raw byte buffer into message
dicts; every message carries its absolute byte offset so the FPGA parser
(0.3.x) can be diffed against this model line by line.

Usage:
    from itch5.parser import iter_messages
    for msg in iter_messages(buf):
        ...
"""
from . import spec


class ItchParserError(Exception):
    """Raised on truncated buffer / unknown message type / bad length."""


def _u(buf: bytes, off: int, n: int) -> int:
    return int.from_bytes(buf[off:off + n], "big")


def _s(buf: bytes, off: int, n: int) -> str:
    return buf[off:off + n].decode("ascii", errors="replace").rstrip(" ")


def parse_header(buf: bytes, off: int) -> dict:
    if off + 11 > len(buf):
        raise ItchParserError(f"truncated header at offset {off}")
    mtype = chr(buf[off])
    if mtype not in spec.LENGTHS:
        raise ItchParserError(
            f"unknown message type {mtype!r} (0x{buf[off]:02x}) at offset {off}")
    total = spec.LENGTHS[mtype]
    if off + total > len(buf):
        raise ItchParserError(
            f"truncated {mtype!r} message at offset {off}: "
            f"need {total} bytes, have {len(buf) - off}")
    return {
        "type": mtype,
        "stock_locate": _u(buf, off + 1, 2),
        "tracking": _u(buf, off + 3, 2),
        "ts_ns": _u(buf, off + 5, 6),
        "_off": off,
        "_len": total,
    }


def parse_message(buf: bytes, off: int) -> dict:
    """Parse one message at `off`; returns dict with header + decoded body."""
    h = parse_header(buf, off)
    mtype = h["type"]
    b = off + 11  # body start
    msg = dict(h)

    if mtype == "S":
        msg["event"] = chr(buf[b])
    elif mtype in ("A", "F"):
        msg.update(order_ref=_u(buf, b, 8), side=chr(buf[b + 8]),
                   shares=_u(buf, b + 9, 4), stock=_s(buf, b + 13, 8),
                   price=_u(buf, b + 21, 4))
        if mtype == "F":
            msg["attribution"] = _s(buf, b + 25, 4)
    elif mtype == "E":
        msg.update(order_ref=_u(buf, b, 8), exec_shares=_u(buf, b + 8, 4),
                   match=_u(buf, b + 12, 8))
    elif mtype == "C":
        msg.update(order_ref=_u(buf, b, 8), exec_shares=_u(buf, b + 8, 4),
                   match=_u(buf, b + 12, 8), printable=chr(buf[b + 20]),
                   exec_price=_u(buf, b + 21, 4))
    elif mtype == "X":
        msg.update(order_ref=_u(buf, b, 8), cancel_shares=_u(buf, b + 8, 4))
    elif mtype == "D":
        msg.update(order_ref=_u(buf, b, 8))
    elif mtype == "U":
        msg.update(orig_ref=_u(buf, b, 8), new_ref=_u(buf, b + 8, 8),
                   new_shares=_u(buf, b + 16, 4), new_price=_u(buf, b + 20, 4))
    elif mtype == "P":
        msg.update(order_ref=_u(buf, b, 8), side=chr(buf[b + 8]),
                   shares=_u(buf, b + 9, 4), stock=_s(buf, b + 13, 8),
                   price=_u(buf, b + 21, 4), match=_u(buf, b + 25, 8))
    elif mtype == "Q":
        msg.update(shares=_u(buf, b, 8), stock=_s(buf, b + 8, 8),
                   cross_price=_u(buf, b + 16, 4), match=_u(buf, b + 20, 8),
                   cross_type=chr(buf[b + 28]))
    elif mtype == "B":
        msg.update(match=_u(buf, b, 8))
    elif mtype == "H":
        msg.update(stock=_s(buf, b, 8), state=chr(buf[b + 8]),
                   reason=_s(buf, b + 10, 4))
    # administrative types: header only, body opaque
    return msg


def iter_messages(buf: bytes, start: int = 0):
    """Yield messages until buffer end; raises ItchParserError on corruption."""
    off = start
    n = len(buf)
    while off < n:
        msg = parse_message(buf, off)
        yield msg
        off += msg["_len"]
