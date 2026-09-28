# SPEC — Agentic FPGA Design Pipeline for Trading Workloads (v0.2, 2026-09-27)

> Project spec (G0 artifact of the SDD process). Frozen as the development and
> acceptance basis for 0.0.1–0.1.0. Version history: v0.1 voided, v0.2 current.
> 中文版为权威原稿的整理转写（原稿为 Word 文档）。

## 0. Version roadmap (semantic versioning)

Strategy: small, independently deliverable milestones. No order book before 0.1.0.

| Version | Scope | Positioning |
|---|---|---|
| 0.0.1 | WSL2 + Bambu + cocotb + Verilator toolchain installed; official example C→RTL→simulation PASS | Milestone |
| 0.1.0 | EMA+RSI streaming kernel: agentic loop (GLM writes C → Bambu synthesis → co-simulation vs NumPy reference → iterate) + CPU-vs-RTL benchmark + full report | Semester deliverable |
| 0.2.x | order book matching kernel (fixed-point entry point) | Long-term |
| 0.3.x+ | tick-to-trade core, multi-kernel benchmarks, (optional) real board | Long-term |
| 1.0.0 | Tradeable HFT tool — open-source "algorithms straight into logic gates" | North star |

## 1. Problem statement

Hypothesis: with an LLM agent + open-source HLS, a finance student with zero
hardware background can turn trading logic (C) into verifiable digital circuits
within days, and quantify the speedup potential vs CPU implementations.
This is the "second boot" of engineering automation, and the open-source
everyman's version of the Algo-Logic route.

Key thesis: have the LLM write **C, not Verilog**, directly bypassing the
dominant failure mode of LLM RTL generation (lack of RTL knowledge).

## 2. Competitive landscape (2026-09-27)

| School | Representatives | Approach | Difference |
|---|---|---|---|
| Closed-loop verification | AutoChip (NVIDIA), RTLFixer, VeriReason, VeriCoder | LLM writes Verilog + compiler/sim feedback loop (RTLFixer 98.5% repair) | All bypass HLS; agent needs RTL knowledge |
| HLS applications | neural-network-fpga, rust_hls, HLS-LAB | Hand-written C → Bambu → board | No LLM/agentic component |
| Benchmarks | VerilogEval, PyHDL-Eval, HaVen (DATE'25) | Evaluate LLM Verilog ability (GPT-4 Turbo ~72% pass) | Evaluate only, no pipeline |

Empty niche: agentic × HLS × trading workloads.

## 3. Scope (0.1.0)

In scope:
- Environment: WSL2 + Ubuntu (Docker fallback); Bambu + cocotb + Verilator, all open source, zero license
- One demo kernel: streaming indicators (EMA + RSI, floating point, 1e-4 relative tolerance)
- Agentic loop: GLM generates/modifies C → Bambu synthesizes RTL → cocotb co-simulation vs NumPy reference → feedback with synthesis+sim logs (≤10-round fuse), full version trail persisted
- Benchmark: CPU vs RTL (simulation-cycle-derived throughput/latency + Bambu resource report)
- Deliverables: experiment report (Markdown + PDF) + open-source GitHub repo

Out of scope (backlog): order book (0.2.x), fixed-point Q16.16, real FPGA board (optional ~$150), timing closure/P&R (OpenROAD), multi-agent, large benchmark sweeps.

## 4. Known pitfalls & mitigations (verified 2026-09)

- ~30% of LLM-Verilog errors only surface at Yosys elaboration → HLS route avoids structurally; feedback loop still carries full Bambu synthesis logs
- Bambu float has soft/hard modes → run official float benchmarks first in 0.0.1; EMA/RSI parameters explicit
- HLS limits: no recursion, dynamic memory → EMA/RSI scalar streaming avoids all
- GPT-4-class single-shot Verilog pass ~72% → closed-loop iteration mandatory; iteration trails are report material
- Bambu is Linux-only → WSL2 primary, Docker/Codespaces fallback
- (2026-09-27 addition) official apt repo domain NXDOMAIN → AppImage route + scripted fixes (see setup/)

## 5. Acceptance criteria (0.1.0)

| Item | Criterion |
|---|---|
| 0.0.1 environment | Toolchain complete; official example C→RTL→simulation PASS |
| Functional | EMA+RSI kernel: ≥1000 random ticks co-simulation, relative error < 1e-4 |
| Agentic convergence | From blank/broken start, ≤10 iterations to functionally correct RTL; trail inspectable |
| Benchmark | ≥1 CPU-vs-RTL throughput/latency table + resource table |
| Open-source delivery | Public repo: 5-min reproducible README + full iteration trail + report |
| Gates | G1: ruff/mypy on pipeline Python; G2: pandera on result tables |

## 6. Risks & fallbacks

| Risk | Mitigation |
|---|---|
| WSL2 blocked | Docker → GitHub Codespaces (free 60h/mo) |
| Float QoR poor | Integer inputs (price×1000) to bypass float |
| Agent doesn't converge | 10-round fuse + human takeover; "what the agent can/can't fix" is report material |
| Semester squeeze | 0.1.0 no hard DDL; 0.0.1 itself is a valuable checkpoint |
| Floor version | Semi-automatic (human review each round) pipeline + CPU-vs-RTL table = minimum viable deliverable |

## 7. Outputs

- Code: pipeline (Windows-side entry + WSL-side runner), pushed to public GitHub repo
- Data: iteration trail (version × error × fix action), CPU-vs-RTL tables, Bambu resource reports
- Report: methods, trail analysis, error taxonomy, conclusions

## 8. Gates configuration

G0 (this spec, human-approved) + G1 (ruff/mypy) + G2 (pandera). Report is static text+figures; no G3/G4/G5.
