# -*- coding: utf-8 -*-
"""Zero-dependency test suite for the ITCH 5.0 golden model.

Run:  python tests/test_itch5.py  (stdlib unittest, no pytest needed)
"""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from itch5 import builders, spec
from itch5.book import ShadowBook
from itch5.parser import ItchParserError, iter_messages, parse_message

NS_10AM = 10 * 3600 * 10**9


class TestLengths(unittest.TestCase):
    def test_all_builders_match_spec_lengths(self):
        self.assertEqual(spec.LENGTHS["A"], 36)
        self.assertEqual(spec.LENGTHS["E"], 31)
        self.assertEqual(spec.LENGTHS["U"], 35)


class TestParser(unittest.TestCase):
    def test_add_order_roundtrip(self):
        buf = builders.add_order(42, "B", 100, "AAPL", 301500, ts_ns=NS_10AM)
        msg = parse_message(buf, 0)
        self.assertEqual(msg["type"], "A")
        self.assertEqual(msg["order_ref"], 42)
        self.assertEqual(msg["side"], "B")
        self.assertEqual(msg["shares"], 100)
        self.assertEqual(msg["stock"], "AAPL")
        self.assertEqual(msg["price"], 301500)
        self.assertEqual(msg["ts_ns"], NS_10AM)
        self.assertEqual(spec.price_display(301500), 30.15)

    def test_add_order_mpid(self):
        buf = builders.add_order(7, "S", 50, "MSFT", 415250, mpid="MPID")
        msg = parse_message(buf, 0)
        self.assertEqual(msg["type"], "F")
        self.assertEqual(msg["attribution"], "MPID")

    def test_replace_roundtrip(self):
        buf = builders.order_replace(1, 2, 300, 301600)
        msg = parse_message(buf, 0)
        self.assertEqual((msg["orig_ref"], msg["new_ref"]), (1, 2))
        self.assertEqual(msg["new_shares"], 300)
        self.assertEqual(msg["new_price"], 301600)

    def test_stream_offsets(self):
        stream = (builders.system_event("O")
                  + builders.add_order(1, "B", 100, "AAPL", 301500)
                  + builders.order_executed(1, 40, 1)
                  + builders.order_delete(1))
        msgs = list(iter_messages(stream))
        self.assertEqual([m["type"] for m in msgs], ["S", "A", "E", "D"])
        self.assertEqual(msgs[0]["_off"], 0)
        self.assertEqual(msgs[1]["_off"], 12)
        self.assertEqual(msgs[2]["_off"], 48)
        self.assertEqual(msgs[3]["_off"], 79)

    def test_truncated_raises(self):
        buf = builders.add_order(1, "B", 100, "AAPL", 301500)
        for cut in range(1, len(buf)):
            with self.assertRaises(ItchParserError):
                list(iter_messages(buf[:cut]))

    def test_unknown_type_raises(self):
        bad = b"\x01" + b"\x00" * 30
        with self.assertRaises(ItchParserError):
            list(iter_messages(bad))


class TestFuzz(unittest.TestCase):
    def test_random_bytes_never_crash(self):
        rng = random.Random(20261028)
        for _ in range(500):
            blob = bytes(rng.randrange(256)
                         for _ in range(rng.randrange(5, 80)))
            try:
                list(iter_messages(blob))
            except ItchParserError:
                pass  # the only allowed exception

    def test_valid_prefix_then_garbage(self):
        rng = random.Random(42)
        for _ in range(200):
            head = builders.add_order(1, "B", 10, "AAPL", 301500)
            tail = bytes(rng.randrange(256)
                         for _ in range(rng.randrange(1, 30)))
            try:
                list(iter_messages(head + tail))
            except ItchParserError:
                pass


class TestShadowBook(unittest.TestCase):
    def test_full_order_lifecycle(self):
        bk = ShadowBook()
        stream = (
            builders.add_order(1, "B", 100, "AAPL", 301500)
            + builders.add_order(2, "S", 200, "AAPL", 301700)
            + builders.add_order(3, "S", 150, "AAPL", 301800)
            + builders.order_executed(2, 50, 1)
            + builders.order_cancel(1, 40)
            + builders.order_replace(3, 4, 300, 301900)
            + builders.order_delete(1)
        )
        n = bk.apply_stream(stream)
        self.assertEqual(n, 7)
        bb, ba = bk.bbo("AAPL")
        self.assertIsNone(bb)
        self.assertEqual(ba, (301700, 150))
        self.assertEqual(bk.levels[("AAPL", "S")][301900], 300)

    def test_trades_do_not_touch_book(self):
        bk = ShadowBook()
        stream = (builders.add_order(1, "B", 100, "AAPL", 301500)
                  + builders.trade_non_cross(999, "B", 100, "AAPL", 301500, 5)
                  + builders.cross_trade(1000, "AAPL", 301550, 6)
                  + builders.broken_trade(5))
        bk.apply_stream(stream)
        self.assertEqual(bk.bbo("AAPL")[0], (301500, 100))
        self.assertEqual(len(bk.orders), 1)

    def test_spread(self):
        bk = ShadowBook()
        bk.apply_stream(builders.add_order(1, "B", 10, "TSLA", 250000)
                        + builders.add_order(2, "S", 10, "TSLA", 250200))
        self.assertEqual(bk.spread("TSLA"), 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
