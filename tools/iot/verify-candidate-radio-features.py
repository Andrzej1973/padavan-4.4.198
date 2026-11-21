#!/usr/bin/env python3
"""Check required implemented radio functions in the exact staged module."""
import argparse,json,runpy
from pathlib import Path
base=Path(__file__).resolve().parents[1]
kvr=runpy.run_path(str(base/'verify-wifi-kvr-image.py'))
REQUIRED=tuple(kvr['SYMBOLS'])+('BndStrg_MsgHandle','APUpdateBeaconFrame','BcnTxSHandler')
def verify(config,symbols):
 checks=kvr['config_checks'](config)
 for option in ('CONFIG_MT7603E_BAND_STEERING_7603','CONFIG_RT_BAND_STEERING'):
  checks[option]=config.splitlines().count(option+'=y')==1
 defined=set()
 for line in symbols.splitlines():
  parts=line.split()
  if len(parts)>=8 and parts[0].endswith(':') and parts[3]=='FUNC' and parts[6]!='UND':
   try:size=int(parts[2])
   except ValueError:continue
   if size>0:defined.add(parts[7])
 missing=sorted(set(REQUIRED)-defined)
 if not all(checks.values()) or missing:raise ValueError('Candidate radio features missing: '+str({'config':checks,'symbols':missing}))
 return {'required_config_checks':checks,'required_code_symbols':list(REQUIRED),
         'radio_feature_code_verified':True,'physical_runtime_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('config',type=Path);p.add_argument('symbols',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 if a.report.exists():raise SystemExit('Report exists')
 a.report.write_text(json.dumps(verify(a.config.read_text(),a.symbols.read_text()),indent=2)+'\n')
 print('PASS staged candidate KVR/Band Steering/beacon/TxS code and configuration; interoperability/runtime unverified')
