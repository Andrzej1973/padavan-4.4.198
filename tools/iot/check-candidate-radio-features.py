"""Reject symbol mentions, undefined/zero/data records and missing config."""
from pathlib import Path
import runpy
here=Path(__file__).resolve().parent
m=runpy.run_path(str(here/'verify-candidate-radio-features.py'));verify=m['verify'];names=m['REQUIRED']
config='\n'.join(n+'=y' for n in tuple(m['kvr']['OPTIONS'])+('CONFIG_MT7603E_BAND_STEERING_7603','CONFIG_RT_BAND_STEERING'))
symbols='\n'.join(f' {i}: 00001000 32 FUNC GLOBAL DEFAULT 1 {name}' for i,name in enumerate(names))
assert verify(config,symbols)['radio_feature_code_verified']
for damaged in [symbols.replace('FUNC','OBJECT',1),symbols.replace('DEFAULT 1','DEFAULT UND',1),symbols.replace(' 32 FUNC',' 0 FUNC',1),symbols.replace(names[0],names[0]+'_wrong',1)]:
 try:verify(config,damaged)
 except ValueError:pass
 else:raise AssertionError('Non-code symbol accepted')
try:verify(config.replace('CONFIG_RT_BAND_STEERING=y','# CONFIG_RT_BAND_STEERING is not set'),symbols)
except ValueError:pass
else:raise AssertionError('Disabled steering accepted')
print('PASS candidate radio feature gate: defined code only, missing/undefined/zero/data/config refusals; synthetic symbol table only')
