#!/usr/bin/env python3
"""Fail-closed WR1200JS CAKE inclusion/default gate; ELF checks remain in CI."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy

HERE=Path(__file__).resolve().parent
read_config=runpy.run_path(str(HERE/'verify-wr1200js-config.py'))['read_config']

def check(tree):
    manifest=json.loads((HERE/'board-capabilities/wr1200js-cake.json').read_text())
    config=read_config(tree/'trunk/.config');kernel=read_config(tree/'trunk/linux-4.4.x/.config')
    romfs=tree/'trunk/romfs';defaults=(tree/'trunk/user/shared/defaults.c').read_text()
    checks={'profile_included':config.get(manifest['selector'])==manifest['included'],
      'kernel_components':all(kernel.get(k)==v for k,v in manifest['kernel_required'].items()),
      'not_default_qdisc':kernel.get('CONFIG_DEFAULT_NET_SCH')!='"cake"' and kernel.get('CONFIG_DEFAULT_CAKE')!='y',
      'factory_off':all(re.search(r'\{\s*"'+re.escape(k)+r'"\s*,\s*"'+re.escape(v)+r'"\s*\}',defaults) for k,v in manifest['factory_default'].items())}
    for name in manifest['modules']:
        matches=list((romfs/'lib/modules').rglob(name))
        checks[name]=len(matches)==1 and matches[0].is_file() and matches[0].stat().st_size>0
    for name in ['bin/tc','bin/ip','usr/lib/sqm/run.sh','www/'+manifest['classic_page']]:
        path=romfs/name;checks[name]=path.is_file() and path.stat().st_size>0
    installed=romfs/'usr/lib/sqm/run.sh';expected=HERE.parent/'overlay/padavan-4.4/ports/sqm/run.sh'
    checks['reviewed_lifecycle']=installed.is_file() and installed.read_bytes()==expected.read_bytes()
    source=(tree/'trunk/user/rc/services.c').read_text()
    checks['start_requires_enable']='nvram_get_int("sqm_enable") != 1 || get_ap_mode()' in source
    return {'board':manifest['board'],'scope':'Effective config, ROMFS presence, reviewed script and factory defaults; separate ELF gates and physical runtime required',
            'status':manifest['status'],'checks':checks,'manifest_sha256':hashlib.sha256((HERE/'board-capabilities/wr1200js-cake.json').read_bytes()).hexdigest(),'runtime_verified':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('tree',type=Path);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    report=check(args.tree);args.report.write_text(json.dumps(report,indent=2)+'\n')
    failed=[k for k,v in report['checks'].items() if not v]
    if failed:raise SystemExit('CAKE inclusion/default gate failed: '+', '.join(failed))
    print('PASS CAKE included, factory OFF and required image paths; runtime unverified')
if __name__=='__main__':main()
