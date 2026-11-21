#!/usr/bin/env python3
"""Self-contained WR1200JS DTS/partition/image-size contract for candidate CI."""
import ast,re,json,argparse
from pathlib import Path

def local_file(root,name):
 p=root/name
 if not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
  raise ValueError('Missing or escaping WR1200JS input: '+name)
 return p

def validate_wr_layout(root):
 base='overlay/padavan-4.4/trunk/linux-4.4.x/arch/mips/boot/dts/ralink/'
 dts=local_file(root,base+'wr1200js.dts').read_text()
 layout=local_file(root,base+'mt7621-spi-16m-wr1200js-layout.dtsi').read_text()
 if '#include "mt7621-spi-16m-wr1200js-layout.dtsi"' not in dts or 'model = "YouHua WR1200JS";' not in dts:raise ValueError('WR1200JS DTS model/include drift')
 partitions={name:(int(offset,16),int(size,16)) for name,offset,size in re.findall(r'label\s*=\s*"([^"]+)";\s*reg\s*=\s*<(0x[0-9a-f]+)\s+(0x[0-9a-f]+)>',layout)}
 expected={'Bootloader':(0,0x30000),'Config':(0x30000,0x10000),'Factory':(0x40000,0x10000),'firmware':(0x50000,0xf70000),'Storage':(0xfc0000,0x40000),'ALL':(0,0x1000000)}
 if partitions!=expected:raise ValueError('WR1200JS SPI16M image/Factory layout drift')
 verifier=local_file(root,'overlay/padavan-4.4/scripts/verify-wr1200js-image.py')
 gates=[node for node in ast.walk(ast.parse(verifier.read_text())) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='add_argument' and any(isinstance(arg,ast.Constant) and arg.value=='--max-size' for arg in node.args)]
 defaults=[kw.value.value for node in gates for kw in node.keywords if kw.arg=='default' and isinstance(kw.value,ast.Constant)]
 if defaults!=[expected['firmware'][1]]:raise ValueError('Image gate/partition size mismatch')
 return partitions

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
 print(json.dumps(validate_wr_layout(a.root),sort_keys=True))
