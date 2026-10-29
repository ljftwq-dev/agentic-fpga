# ROADMAP v0.3 — "Real Trading Infrastructure" Redirect

> Decision date: 2026-10-28 · Supersedes the roadmap table in SPEC-v0.2 (spec body unchanged; only the roadmap ladder is extended).
> Decision: this project builds **real trading infrastructure**, not a portfolio piece.

## Positioning (the one-paragraph version)

The software stack — data pipelines → signals → execution → risk → nightly review — is the *body*; the FPGA is an **acceleration module** inserted into the data-ingest → signal → order segment. A microsecond only matters after there is a signal worth reacting to: the event-driven alpha layer (fundamental surprise prediction) decides *what* to trade; this project decides *how fast* the machinery can honor it.

## Milestone ladder

| Version | Scope | Status |
|---|---|---|
| 0.0.1 | Toolchain + official example PASS | ✅ done 2026-09-27 |
| 0.1.0 | EMA+RSI kernel; agentic loop; CPU vs RTL benchmark | 🚧 semester goal (unchanged) |
| 0.2.x | **ITCH 5.0 feed handler** + order book kernel (fixed-point). Golden Python reference model delivered early: `itch5/` — parser + builders + shadow book + stats CLI, 12/12 tests, 700-case fuzz clean | ✅ golden model 2026-10-28 · FPGA side = winter |
| 0.3.x | **Host bridge**: FPGA/WSL side feeds the live Python executor (order-placing stack already running in production for the paper account) — tick-to-trade demo with measured end-to-end latency | winter–spring |
| 1.0.0 | Tradeable tool | north star |

## Honest constraints, stated up front

- **US equities microstructure is not our game**: colo + queue position + direct feeds cost more than the strategy would earn. We do not pretend otherwise.
- **The realistic end-to-end arena for an FPGA at retail scale is crypto cross-venue**: free market-data feeds, cheap colo, 24/7 markets. When 0.3.x works on simulated data, that is where it graduates to real bytes.
- **130 nm / open-source toolchains top out far below HFT-class frequencies.** The claim this project can honestly make is *orders-of-magnitude latency reduction vs. the software baseline we control*, plus the automation thesis — not parity with FPGA-armed prop desks.

## How the pieces connect

```
(event alpha layer decides WHAT)      (this repo decides HOW FAST)
revenue-model → surprise signal  ──►  ITCH feed → FPGA book → trigger ──►  host bridge ──►  executor
                                        0.2.x            0.2.x              0.3.x            (already live)
```

## Next actions (in order)

1. [ ] 0.1.0 as planned: EMA+RSI agentic loop (semester goal, unaffected by this redirect)
2. [ ] Validate `itch5/` against a real NASDAQ TotalView sample file (`python -m itch5.stats <file>`) — parser is synthetic-tested only until this happens
3. [ ] Bambu C kernel: parse the core ITCH message set (S/A/E/C/X/D/U) in HLS-friendly C, co-simulated against `itch5` as the golden model — the same cross-check discipline as our econometrics pipeline (R↔Python), now software↔hardware
4. [ ] Fixed-point order book levels in C → RTL, diffed against `itch5.book.ShadowBook`
5. [ ] Host bridge prototype: shared-memory/UDP link into the live paper executor, measure end-to-end latency vs. pure-Python path
6. [ ] Easter egg (unchanged): TinyTapeout car-pool tapeout rides the same C→Bambu→OpenROAD path
