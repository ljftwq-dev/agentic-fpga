#!/bin/bash
# bambu_appimage_fix.sh — make the extracted Bambu AppImage (PandA 2024.10) work
# on modern Ubuntu (24.04/26.04, GCC 14/15 era).
#
# The official apt repo (bambu.polimi.it) no longer resolves (NXDOMAIN as of
# 2026-09), so the AppImage from https://release.bambuhls.eu/ is the practical
# install path. It hardcodes /usr paths and assumes an Ubuntu-18.04-era
# toolchain; this script applies all nine fixes (6 synthesis + 3 simulation).
#
# Usage (inside WSL/Linux, after extracting the AppImage):
#   wget -c https://release.bambuhls.eu/bambu-latest.AppImage
#   chmod +x bambu-latest.AppImage && ./bambu-latest.AppImage --appimage-extract
#   # => produces ./squashfs-root  (move it to ~/tools/ or set APPDIR below)
#   sudo bash bambu_appimage_fix.sh [path/to/squashfs-root]
set -e

APPDIR="${1:-$HOME/tools/squashfs-root}"
if [ ! -d "$APPDIR" ]; then
  echo "ERROR: $APPDIR not found. Pass the squashfs-root path as argument." >&2
  exit 1
fi
APPDIR=$(readlink -f "$APPDIR")
echo "Using APPDIR=$APPDIR"

# ---------- A. Synthesis flow (HLS frontend) ----------
ln -sfn "$APPDIR/usr/share/panda" /usr/share/panda
ln -sfn "$APPDIR/usr/lib/panda"    /usr/lib/panda
ln -sfn "$APPDIR/usr/bin/clang-16"   /usr/bin/clang-16
ln -sfn "$APPDIR/usr/bin/clang++-16" /usr/bin/clang++-16
# NOTE: must point at the bundled clang under usr/bin/, NOT the vanilla
# LLVM-16 release also shipped in the image (it lacks the -panda-* options).
ln -sfn "$APPDIR/lib/x86_64-linux-gnu/libtinfo.so.5" /usr/lib/x86_64-linux-gnu/libtinfo.so.5
ln -sfn "$APPDIR/usr/gcc_plugins" /usr/gcc_plugins
ln -sfn "$APPDIR/usr/lib/libbdd.so.0" /usr/lib/x86_64-linux-gnu/libbdd.so.0

# ---------- B. Simulation flow (mdpi C-RTL co-simulation) ----------
# B1. Old clang-16 does not know GCC>=13 platform header layout; copy the
#     platform bits headers next to the generic ones.
#     (NOTE: /usr/include/c++/15/bits is a REAL directory — you cannot
#      symlink over it; `ln -sfn` would nest a link INSIDE it.)
for gxx in /usr/include/c++/*; do
  ver=$(basename "$gxx")
  if [ -d "/usr/include/x86_64-linux-gnu/c++/$ver/bits" ]; then
    cp -n "/usr/include/x86_64-linux-gnu/c++/$ver/bits/"*.h "/usr/include/c++/$ver/bits/" 2>/dev/null || true
  fi
done
# B2. libstdc++ dev links (64-bit and 32-bit; bambu testbenches link with -m32)
for gccv in /usr/lib/gcc/x86_64-linux-gnu/*/; do
  [ -e "$gccv/libstdc++.so" ] && ln -sfn "$gccv/libstdc++.so" /usr/lib/x86_64-linux-gnu/libstdc++.so || true
  [ -e "${gccv}32/libstdc++.so" ] && ln -sfn "${gccv}32/libstdc++.so" /usr/lib32/libstdc++.so || true
done
ldconfig

# ---------- C. apt deps (idempotent) ----------
export DEBIAN_FRONTEND=noninteractive
apt-get install -y -qq gcc-multilib g++-multilib iverilog verilator > /dev/null 2>&1 || \
  apt-get install -y gcc-multilib g++-multilib iverilog verilator

echo "=== All fixes applied. Verify with:"
echo "    bambu adpcm.c --simulate -fwhole-program -fno-delete-null-pointer-checks"
echo "    (PATH must include $APPDIR/usr/bin)"
