# -*- coding: utf-8 -*-
"""ITCH 5.0 message spec table (NASDAQ TotalView-ITCH protocol).

Total message lengths (including the 11-byte header). Core trading set is
hard-verified against the official spec; administrative messages are parsed
as opaque bodies with known lengths.

Header (11 bytes):
    Message Type      1 byte  printable ASCII
    Stock Locate      2 bytes unsigned big-endian
    Tracking Number   2 bytes unsigned big-endian
    Timestamp         6 bytes unsigned big-endian (ns since midnight)

Price fields: 4-byte unsigned big-endian integer, implied 4 decimals
(divide by PRICE_SCALE = 10_000). Kept as raw ints everywhere; use
price_display() only for presentation (avoids float contamination).
"""

PRICE_SCALE = 10_000

# total message length in bytes (header included)
LENGTHS = {
    "S": 12,   # System Event
    "F": 40,   # Add Order (MPID Attribution)
    "A": 36,   # Add Order (No MPID)
    "E": 31,   # Order Executed
    "C": 36,   # Order Executed With Price
    "X": 23,   # Order Cancel
    "D": 19,   # Order Delete
    "U": 35,   # Order Replace
    "P": 44,   # Trade (Non-Cross)
    "Q": 40,   # Cross Trade
    "B": 19,   # Broken Trade
    "H": 25,   # Stock Trading Action
    "Y": 39,   # Stock Directory
    "L": 26,   # Market Participant Position
    "V": 35,   # MWCB Decline Level
    "W": 12,   # MWCB Status
    "K": 28,   # IPO Quoting Period Update
    "J": 35,   # LULD Auction Collar
    "h": 21,   # Operational Halt
}

# message types whose full body layout is decoded by parser.py
DECODED = frozenset("SAFE CXDUPQBH".replace(" ", ""))


def price_display(raw: int) -> float:
    """Render a raw ITCH price int for humans only (never for math)."""
    return round(raw / PRICE_SCALE, 4)
