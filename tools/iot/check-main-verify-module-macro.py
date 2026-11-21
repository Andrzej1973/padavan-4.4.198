#!/usr/bin/env python3
"""Compile actual main VERIFY branch with the vendor module-release macros."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("candidate", type=Path)
p.add_argument("--compiler", default="gcc")
a = p.parse_args()
source = (a.candidate / "os/linux/rt_main_dev.c").read_text()
start = source.index("  if (closed)")
end = source.index("  return -1;", start)
arm = source[start:end]
assert "if (closed) {" in arm and "} else if" in arm
header = (a.candidate / "include/os/rt_linux.h").read_text()
macros = re.findall(r"^#define RT_MOD_DEC_USE_COUNT\(\)([^\n]+)", header, re.M)
assert macros and all(m.rstrip().endswith(";") for m in macros)
prefix = """#define THIS_MODULE 0
#define MOD_DEC_USE_COUNT module_put(0)
#define DBGPRINT(level,args) do {} while(0)
#define RT_DEBUG_ERROR 0
#define NULL ((void*)0)
struct wr_iot_radio_ticket { int value; };
void module_put(int n);
int wr_iot_main_verify_recovery_submit(int adapter,int net_dev,unsigned long generation,struct wr_iot_radio_ticket *ticket);
int check(int closed,int began,unsigned long generation,unsigned long close_generation){
int adapter=0,net_dev=0;struct wr_iot_radio_ticket close_ticket;
"""
with tempfile.TemporaryDirectory(prefix="wr-module-macro-") as directory:
    root = Path(directory)
    for i, macro in enumerate(macros):
        code = "#define RT_MOD_DEC_USE_COUNT()" + macro + "\n" + prefix + arm + "return 0;}\n"
        good = root / (str(i) + ".c")
        good.write_text(code)
        cmd = [a.compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsyntax-only"]
        subprocess.run(cmd + [str(good)], check=True)
        bad = root / (str(i) + "-bad.c")
        bad.write_text(code.replace("if (closed) {", "if (closed)").replace("} else if", "else if"))
        result = subprocess.run(cmd + [str(bad)], capture_output=True, text=True)
        assert result.returncode != 0 and "else" in result.stderr, result.stderr
print("PASS actual main VERIFY branch with vendor module-release macros; unbraced regression rejected")
