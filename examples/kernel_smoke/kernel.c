// Smoke-test kernel for the agentic-fpga toolchain (v0.0.1).
// int math with a multiply-accumulate shape; HLS-friendly (no loops/pointers).
// Synthesize:  bambu kernel.c --top-fname=kernel
int kernel(int a, int b) {
  return a * b + 42;
}
