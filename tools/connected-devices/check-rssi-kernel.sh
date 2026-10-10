#!/bin/bash
# Use a configured, already-built actual target kernel. Never load the probe.
set -euo pipefail
kernel="$(realpath "$1")"
compiler="$(realpath "$2")"
output="$3"
test -x "$compiler"
test -s "$kernel/include/generated/autoconf.h"
test -s "$kernel/vmlinux"
test ! -e "$output"
mkdir -p "$output"
output="$(realpath "$output")"
# The single-object target bypasses the modules target directory setup.
mkdir -p "$output/.tmp_versions"
tools="$(cd "$(dirname "$0")" && pwd)"
cp "$tools/rssi-kernel.h" "$tools/rssi-record.h" "$output/"
cp "$tools/check-rssi-kernel.c" "$output/wr-rssi-kernel-probe.c"
printf '%s\n' 'obj-m := wr-rssi-kernel-probe.o' > "$output/Makefile"
cross="${compiler%gcc}"
make -C "$kernel" ARCH=mips CROSS_COMPILE="$cross" M="$output" wr-rssi-kernel-probe.o
"${cross}readelf" -h "$output/wr-rssi-kernel-probe.o" > "$output/elf.txt"
grep -q 'Machine:.*MIPS' "$output/elf.txt"
printf '%s\n' 'PASS real target kernel RSSI observer compile; no driver integration or runtime claim'
