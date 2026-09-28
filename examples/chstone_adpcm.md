# Reproduce the v0.0.1 acceptance run (CHStone/adpcm)

Prerequisite: toolchain installed and fixed (see README Quick Start).

```bash
git clone --depth 1 https://github.com/ferrandi/CHStone.git
mkdir adpcm && cp CHStone/adpcm/adpcm.c adpcm/ && cd adpcm
bambu adpcm.c --simulate -fwhole-program -fno-delete-null-pointer-checks
```

Expected output:

```
Results file: results.txt
Reset active: LOW
Sim: Testbench returned: 0
- HLS_output/simulation/bambu_testbench.v:278: Verilog $finish
```

`returned: 0` = every output of the generated RTL matches the golden values
built into the CHStone benchmark. `results.txt` contains the printf output of
the testbench (main_result = 0 means zero mismatches).

Numbers from the verified run (2026-09-27, WSL2 Ubuntu 26.04, Bambu 2024.10):

| Metric | Value |
|---|---|
| RTL size | ~45,000 lines Verilog |
| Flip-flops | 9,583 |
| Registers (binding) | 494 |
| 2-to-1 mux equivalents | 285 |
| Simulator | Verilator (auto-detected by bambu) |
