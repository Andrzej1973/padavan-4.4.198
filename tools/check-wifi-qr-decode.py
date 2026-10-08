import sys,json,argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('matrices',type=Path)
parser.add_argument('--dependencies',type=Path)
args=parser.parse_args()
if args.dependencies: sys.path.insert(0,str(args.dependencies.resolve()))
import zxingcpp
from PIL import Image,ImageDraw
cases=json.loads(args.matrices.read_text(encoding='utf-8'))
for case in cases:
 m=case['modules']; n=len(m); scale=8; quiet=4
 image=Image.new('L',((n+quiet*2)*scale,)*2,255); draw=ImageDraw.Draw(image)
 for y,row in enumerate(m):
  for x,dark in enumerate(row):
   if dark: draw.rectangle(((x+quiet)*scale,(y+quiet)*scale,(x+quiet+1)*scale-1,(y+quiet+1)*scale-1),fill=0)
 result=zxingcpp.read_barcode(image)
 assert result is not None,case['index']
 assert result.bytes==case['payload'].encode('utf-8'),(case['index'],result.bytes)
 print('PASS independent QR decode case',case['index'],'matrix',n,'UTF8 bytes',len(result.bytes))
