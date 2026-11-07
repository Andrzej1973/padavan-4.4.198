# IoT v39 versus prepared MT7603 source (2026-10-25)

This is an isolated source integration check, not a target compile or a
production driver install. The prepared tree is
`../iot-source-prepared-20261024/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3`;
the reviewed pinned base is `../iot-pinned-mt76x3-c25283e/mt76x3`.

The v39 overlay has 55 source paths, including 36 paths present in the
pinned base and 19 newly introduced paths. The prepared tree differs from
the pinned base in exactly five overlapping files: `ap/ap.c`, `ap/ap_cfg.c`,
`common/rtmp_init.c`, `hw_ctrl/cmm_asic_mt.c`, and `include/rtmp.h`.

`prepare-v39-merge-manifest.py` verified all 31 source blobs from the
previous reviewed manifest against the pinned base, then recorded SHA-256
for every v39 candidate file and Git blobs for the 36 original files. The
manifest is `.iot-local-check/aux-remove-close-v39-manifest.json`.

The fail-closed assembler now permits the reviewed 55/36 v39 shape as well
as its earlier 46/32 shape. It created `../iot-merged-v39-20261025`, merging
the five overlapping files; the one expected adapter-initialization text
conflict was resolved under the existing exact-marker rule. Independent
readback matched every one of the 55 output SHA-256 values in
`../iot-merged-v39-20261025.manifest.json`; no conflict marker remained.
The merged tree retains both RSSI and IoT adapter initialization and the
v39 `CLOSING` removal refusal.

The local Windows environment exposes no installed WSL distribution or
usable MIPS cross compiler. The optional GitHub candidate workflow compiles
the older committed candidate, not this uncommitted v39 tree. Therefore
`target_compiled=false`, `production_installed=false`, and
`runtime_verified=false` remain true. Before a target compile, the v39
source must enter a reproducible CI input without sweeping unrelated dirty
files into the build. The PCI retirement owner still needs real driver
operations and failure-path tests before production installation.
