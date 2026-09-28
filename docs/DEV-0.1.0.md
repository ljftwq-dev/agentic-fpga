# 0.1.0 Development Notes — M1 Design (frozen decisions)

> Decisions confirmed 2026-09-27 with the project owner. This file is the
> working reference for M1 implementation; update via commit history.

## Frozen decisions

| Decision | Choice | Rationale |
|---|---|---|
| Float precision | `float` (IEEE-754 binary32) | 1e-4 relative tolerance is well within float; halves HLS resources vs double |
| Kernel interface | **streaming, one tick per call** | HFT semantics; state lives in hardware registers; matches SPEC "流式技术指标" |
| M2 agentic start | **broken start** | Seed GLM with a subtly buggy C; the repair trajectory demonstrates the feedback loop better than blank slate |

## M1 scope (manual baseline — no LLM in the loop yet)

Build the measuring stick first: hand-written C kernel, NumPy reference,
cocotb harness, all green, before agentic automation (M2).

### Kernel interface (`pipeline/ema_rsi.c`)

```c
// EMA(N=20, alpha=2/(N+1)) and RSI(N=14, Wilder) over a price stream.
// One call = one tick. State persists in static variables -> synthesized
// into registers by Bambu.
//
// Warmup contract (must match ref_model.py EXACTLY):
//   tick 1        : ema = price        (seed)
//   ticks 1..N_rsi: rsi = 50.0         (defined output during warmup)
//   tick > N_rsi  : rsi per Wilder recursion
// Comparison window starts after warmup (tick > max(N_ema, N_rsi) + 1).
void ema_rsi_tick(float price, float* ema_out, float* rsi_out);
```

Implementation notes:
- All coefficients as compile-time constants (`2.0f/(N+1)` etc.) so clang
  folds them into multiplies — no runtime division except the single
  `RSI = 100*ag/(ag+al)` (guarded: if ag+al==0 output 50.0).
- No recursion, no dynamic memory, no libc calls — HLS-clean by construction.

### Reference model (`pipeline/ref_model.py`)

- Tick generator: random walk, fixed seed, ≥1000 ticks (pandera-validated
  table persisted to `data/ticks.parquet`).
- Computes EMA/RSI step-by-step in **float32** (numpy scalar ops kept in
  binary32) so the reference shares the kernel's numeric basis; tolerance is
  for RTL-vs-reference, not precision-of-representation disputes.

### Two independent verification gates

| Gate | Mechanism | Role |
|---|---|---|
| G-inner | `bambu --generate-tb` + XML stimulus (Bambu co-simulates C-behavior vs RTL) | fast inner loop; same mechanism as the 0.0.1 adpcm PASS |
| G-outer | cocotb + Verilator harness (`pipeline/testbench.py`) driven by NumPy reference | **the SPEC acceptance gate** — the ruler is never the device under test |

cocotb/Verilator specifics:
- Bambu maps `float` ports to 32-bit wires; harness converts via
  `struct.pack/unpack('f', ...)` bit-casts.
- Per-tick assertion after warmup: `|rtl - ref| / |ref| < 1e-4`, all ticks.

### Directory plan

```
pipeline/
├── ema_rsi.c        # kernel under test (hand-written in M1, GLM-authored in M2)
├── ref_model.py     # NumPy reference + tick generation (pandera schema)
├── testbench.py     # cocotb harness
├── Makefile         # synth (bambu) + sim (cocotb/Verilator) targets
└── iterations/      # agentic trail (M2): v001/ c_source, synth.log, sim.log, verdict
```

### M1 acceptance checklist

- [ ] ≥1000 ticks, G-inner PASS (`testbench returned: 0`)
- [ ] same ticks, G-outer: every post-warmup tick within 1e-4
- [ ] logs + tick data persisted; `ruff check` / `mypy` clean (G1)

## M2–M4 (outline, unchanged)

- M2: `agent_loop.py` — GLM (zhipu API via secrets_loader) receives broken C +
  compile/synth/sim logs; edits C; re-runs pipeline; ≤10 rounds fuse; full
  trail to `iterations/`.
- M3: CPU-native vs RTL benchmark (sim-cycle-derived throughput/latency) +
  Bambu resource report → tables/figures.
- M4: report, README refresh, CI (G1 on GitHub Actions), tag v0.1.0.

## Working notes / open items

- RSI division: accept the float divider's cost in 0.1.0; revisit only if
  resource report is pathological (SPEC fallback: integer price×1000).
- Schedule: coursework has priority this week (FIN 559 HW5 due Tue);
  M1 kicks off after that — no hard DDL per SPEC.
