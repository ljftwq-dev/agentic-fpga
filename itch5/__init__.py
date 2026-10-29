# -*- coding: utf-8 -*-
"""itch5 — NASDAQ TotalView-ITCH 5.0 golden reference model.

parser  : binary -> message dicts (offset-annotated for FPGA diffing)
builders: semantic fields -> exact-length binary (test inverse of parser)
book    : shadow order book from the A/F/E/C/X/D/U stream
stats   : CLI histogram for real ITCH sample files
spec    : message length table + price conventions
"""
__version__ = "0.1.0"
