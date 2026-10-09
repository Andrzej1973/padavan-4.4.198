#!/usr/bin/env python3
import json,sys
from pathlib import Path
value=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected='<script>'+chr(34)+chr(92)+chr(10)+chr(9)+chr(0xfffd)*2+chr(0x3c0)+chr(0x1f600)+' Пристрій'
assert value['devices'][0]['hostname']==expected
assert value['epoch']=='fixture' and value['sequence']==2
assert value['devices'][0]['networkmapStale'] is False
print('PASS JSON round-trip: quotes, backslash, controls, invalid UTF-8 replacement, Unicode and emoji')
