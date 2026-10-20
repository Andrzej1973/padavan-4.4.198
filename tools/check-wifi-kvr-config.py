#!/usr/bin/env python3
"""Compile the actual transformed KVR emitter and check first-match semantics."""
import argparse
import importlib.util
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("source_file", type=Path)
p.add_argument("--output-dir", type=Path, required=True)
a = p.parse_args()
spec = importlib.util.spec_from_file_location("prepare_kvr", Path(__file__).with_name("prepare-wifi-kvr-config.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original = a.source_file.read_text(encoding="utf-8")
changed = module.transform(original)
for invalid in (changed, original.replace('RRMEnable=%d', 'ChangedRRM=%d', 1)):
    try:
        module.transform(invalid)
    except ValueError:
        pass
    else:
        raise SystemExit("Changed/repeated source preparation was accepted")
start = changed.index("\t/* WR_KVR_SINGLE_RECORD")
end = changed.index("\t//HT_GI", start)
block = changed[start:end]
head = r"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int kv, ft;
static int nvram_wlan_get_int(int band, const char *key) {
 (void)band;
 return strcmp(key, "HT_80211KV") == 0 ? kv : ft;
}
int main(int argc, char **argv) {
 FILE *fp = stdout;
 int i_val, is_aband;
 if (argc != 4) return 2;
 is_aband = atoi(argv[1]); kv = atoi(argv[2]); ft = atoi(argv[3]);
"""
a.output_dir.mkdir(parents=True, exist_ok=True)
for dbdc in (False, True):
    binary = (a.output_dir / ("kvr-dbdc.exe" if dbdc else "kvr-single.exe")).resolve()
    command = ["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-x", "c", "-", "-o", str(binary)]
    if dbdc:
        command.insert(1, "-DBOARD_MT7915_DBDC")
    subprocess.run(command, input=head + block + "return 0; }\n", text=True, check=True)
    for band in (0, 1):
        for kv in (0, 1):
            for ft in (0, 1):
                result = subprocess.check_output([str(binary), str(band), str(kv), str(ft)], text=True)
                records = [line.split("=", 1) for line in result.splitlines()]
                keys = [key for key, value in records]
                if len(keys) != len(set(keys)):
                    raise SystemExit("Duplicate generated key")
                values = dict(records)
                expected = {"RRMEnable": f"{kv};{kv}", "WNMEnable": f"{kv};{kv}",
                            "FtSupport": f"{ft};{ft}" if dbdc else str(ft),
                            "FtOtd": "0;0" if dbdc else "0", "FtRic": "1;1" if dbdc else "1"}
                if values != expected:
                    raise SystemExit("Generated records differ: " + repr(values))
print("PASS: actual KVR emitter, 16 band/flag/DBDC cases; duplicate and drift guards")
