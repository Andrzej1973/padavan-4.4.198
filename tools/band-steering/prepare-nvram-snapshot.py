"""Reject truncated NVRAM dumps and destructive consolidation/flash images."""
import argparse
import hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path)
p.add_argument('--kernel-root',action='store_true',help='Argument is an isolated kernel checkout root')
a=p.parse_args()
kernel=a.source if a.kernel_root else a.source/'trunk/linux-4.4.x'
path=kernel/'drivers/nvram/nvram.c'
s=path.read_text();start=s.index('int\n_nvram_getall(');end=s.index('\n}',start)+2
body=s[start:end]
if hashlib.sha256(body.encode()).hexdigest()!='0d37c18c85a75fd6e6e1981d3637c4686dc0eb18a74a0f19b1537eaaf9f28e9a':
    raise ValueError('Pinned NVRAM getall function changed; no files written')
anchor='\t\t\telse\n\t\t\t\tbreak;'
if body.count(anchor)!=1 or s.count('#include <linux/string.h>\n')!=1:
    raise ValueError('NVRAM dump anchors changed; no files written')
body=body.replace(anchor,'\t\t\telse\n\t\t\t\treturn -ENOSPC; /* Never certify a partial snapshot. */')
s=s[:start]+body+s[end:]
start=s.index('int\n_nvram_generate(');end=s.index('\n}',start)+2
body=s[start:end]
if hashlib.sha256(body.encode()).hexdigest()!='9af4f6a563312299a264f574da10d35bb2b1470625e1a211197adebcb28334f4':
    raise ValueError('Pinned NVRAM generator changed; no files written')
anchor='\t\t\t\tbreak;'
if body.count(anchor)!=1:
    raise ValueError('NVRAM generation overflow anchor changed; no files written')
body=body.replace(anchor,'\t\t\t\treturn -ENOSPC; /* Preserve live tuples and flash on overflow. */')
s=s[:start]+body+s[end:]
s=s.replace('#include <linux/string.h>\n','#include <linux/string.h>\n#include <linux/errno.h>\n')
path.write_text(s)
print('NVRAM dump/generator reject overflow before rehash or flash; existing callers retain errors')
