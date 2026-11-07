#!/usr/bin/env python3
"""Report known MIPS checked-off refusal stub; never infer functional runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("module",type=Path)
p.add_argument("output",type=Path)
p.add_argument("--cross",required=True)
a=p.parse_args()
if a.output.exists():p.error("new report required")
elf=subprocess.check_output([a.cross+"readelf","-h",str(a.module)],text=True)
assert "MIPS" in elf and "little endian" in elf
symbols=subprocess.check_output([a.cross+"nm","-S",str(a.module)],text=True)
line=next(l for l in symbols.splitlines() if l.endswith(" wr_iot_mt_radio_off_checked"))
address,size,kind,name=line.split()
assert kind.upper()=="T"
assembly=subprocess.check_output([a.cross+"objdump","-d","--start-address="+str(int(address,16)),"--stop-address="+str(int(address,16)+int(size,16)),str(a.module)],text=True)
known_refusal=int(size,16)==8 and "03e00008" in assembly and "00001025" in assembly
report={"scope":"known target refusal-stub detection only; non-stub does not prove safety or completion", "module_sha256":hashlib.sha256(a.module.read_bytes()).hexdigest(),"symbol":name,"symbol_bytes":int(size,16),"known_unconditional_false":known_refusal,"shutdown_capability":"unavailable" if known_refusal else "unverified","production_accepted":False,"runtime_verified":False,"disassembly":assembly}
a.output.write_text(json.dumps(report,indent=2)+"\n")
print("Checked radio-off capability:",report["shutdown_capability"])
