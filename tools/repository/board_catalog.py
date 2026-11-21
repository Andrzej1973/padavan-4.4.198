"""Shared board admission validation; boards.json remains the only catalogue."""
import ast,json,re
from pathlib import Path

def local_file(root,name):
 p=Path(name)
 if p.is_absolute() or '..' in p.parts or not name or not (root/p).is_file():raise ValueError('Invalid required file: '+str(name))
 if not (root/p).resolve().is_relative_to(root.resolve()):raise ValueError('Escaping source path: '+name)
 return root/p

def read_config(path):
 values={}
 for line in path.read_text().splitlines():
  match=re.fullmatch(r'(CONFIG_[A-Za-z0-9_]+)=(.*)',line.strip())
  if match:
   k,v=match.groups()
   if k in values and values[k]!=v:raise ValueError('Conflicting config '+k)
   values[k]=v
 return values

def load(root):
 data=json.loads((root/'boards.json').read_text())
 if data.get('schema_version')!=1:raise ValueError('Unsupported board catalogue schema')
 boards=data['boards'];ids=set()
 for b in boards:
  if not re.fullmatch('[a-z0-9-]+',b['id']) or b['id'] in ids:raise ValueError('Invalid/duplicate board ID')
  ids.add(b['id'])
  if type(b['build_enabled']) is not bool:raise ValueError('build_enabled must be boolean')
  config=read_config(local_file(root,b['config']))
  expected=b['id'].upper()
  if config.get('CONFIG_FIRMWARE_PRODUCT_ID','').strip('"')!=expected:raise ValueError('Board product ID/config mismatch: '+b['id'])
  if b['build_enabled']:
   if b['recipe']!='wr1200js' or b['id']!='wr1200js':raise ValueError('No verified reusable recipe for admitted board')
   if config.get('CONFIG_PRODUCT')!='MT7621' or config.get('CONFIG_LINUXDIR')!='linux-4.4.x':raise ValueError('WR1200JS SoC/kernel drift')
   board=root/'overlay/padavan-4.4/trunk/configs/boards/WR1200JS'
   for n in ['board.h','board.mk','kernel-4.4.x.config']:local_file(root,str((board/n).relative_to(root)))
   if not re.search(r'#define\s+BOARD_PID\s+"WR1200JS"',(board/'board.h').read_text()):raise ValueError('Board header ID mismatch')
   kernel=read_config(board/'kernel-4.4.x.config')
   for k,v in {'CONFIG_CPU_MIPS32_R2':'y','CONFIG_PCI':'y','CONFIG_MTD_SPI_NOR':'y','CONFIG_MT7603E_RLT_WIFI':'m'}.items():
    if kernel.get(k)!=v:raise ValueError('Required WR1200JS kernel setting '+k)
   if config.get('CONFIG_FIRMWARE_INCLUDE_SQM')!='y':raise ValueError('WR1200JS CAKE/SQM inclusion required; runtime default is separate')
   validate_wr_layout(root)
  elif b['recipe'] is not None:raise ValueError('Pending board must not carry active recipe')
 return boards

def select(boards,selection):
 ids={b['id'] for b in boards};requested=ids if selection=='all-supported' else set(selection.split(','))
 if requested-ids:raise ValueError('Unknown boards: '+','.join(sorted(requested-ids)))
 selected=[b for b in boards if b['id'] in requested and b['build_enabled']]
 if selection!='all-supported' and len(selected)!=len(requested):raise ValueError('Requested board port is not enabled for firmware builds')
 if not selected:raise ValueError('No supported boards selected')
 return selected

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
