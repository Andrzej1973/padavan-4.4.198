#!/usr/bin/env python3
"""Select the actual paired compiler/binutils, never ccache wrapper aliases."""
from pathlib import Path

def select(prefix):
 prefix=Path(prefix)
 pairs=[(p,p.with_name('mipsel-linux-uclibc-readelf')) for p in prefix.rglob('mipsel-linux-uclibc-gcc') if p.parent.name=='bin']
 pairs=[pair for pair in pairs if all(p.is_file() for p in pair)]
 if len(pairs)!=1:raise ValueError('Expected exactly one bin GCC/readelf pair, got '+str(len(pairs)))
 return pairs[0]
