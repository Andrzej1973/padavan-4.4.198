#!/usr/bin/env python3
"""Execute both composed GTK writer paths with the actual shared arbiter."""
import argparse,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
module=runpy.run_path(str(here/'ra2-key-arbitration-composition.py'))
def fixture_definitions(name,stop):
 source=(here/name).read_text();definitions=source[:source.index(stop)]
 old=sys.argv;sys.argv=[str(here/name),str(a.source.resolve(strict=True))]
 ns={'__file__':str(here/name),'__name__':'fixture_definitions'}
 try:exec(compile(definitions,str(here/name),'exec'),ns)
 finally:sys.argv=old
 return ns
ns=fixture_definitions('check-ra2-gtk-request.py',"with tempfile.TemporaryDirectory(prefix='wr-ra2-gtk-scope-')")
prefix=ns['prefix'].replace('#include "peer-table-owner.h"',
 '#include "peer-table-owner.h"\n#include "ra2-association-owner.h"')
prefix=prefix.replace('struct wr_iot_peer_table_owner wr_iot_peer_table_owner;',
 'struct wr_iot_peer_table_owner wr_iot_peer_table_owner;struct wr_ra2_assoc_owner wr_ra2_assoc_owner;')
main=ns['main'].replace('which<8','which<9').replace(
 '  if(which==7)((PHEADER_802_11)event.Msg)->Addr1[0]=1;',
 '  if(which==7)((PHEADER_802_11)event.Msg)->Addr1[0]=1;\n'
 '  if(which==8)ad.wr_ra2_assoc_owner.associations=1;')
actors=ns['actors'].replace('assert(ad->wr_iot_control_users==1&&ad->wr_iot_ra2_key_active==1);',
 'assert(ad->wr_iot_control_users==1&&ad->wr_iot_ra2_key_active==1);\n'
 '  assert(ad->wr_ra2_assoc_owner.key_active&&!ad->wr_ra2_assoc_owner.associations);\n'
 '  struct wr_ra2_assoc_ticket mutation={0};\n'
 '  assert(!wr_ra2_assoc_enter(&ad->wr_ra2_assoc_owner,&mutation,0));')
request=module['request_header']((here/'ra2-gtk-request-kernel.h').read_text())
# The periodic fixture definitions contain no test runner until __main__.
rekey=fixture_definitions('check-ra2-rekey-path.py',"if __name__ == '__main__':")
timer_source=(a.source/'ap/ap_wpa.c').read_text();start=timer_source.index('VOID GREKEYPeriodicExec(')
native=timer_source[start:timer_source.index('\n}',start)+2]
wrapped=runpy.run_path(str(here/'ra2-rekey-composition.py'))['compose'](native)
wrapped=module['periodic'](wrapped)
timer_prefix=rekey['PREFIX'].replace('#include "ra2-rekey-admission.h"',
 '#include "ra2-rekey-admission.h"\n#include "ra2-association-owner.h"').replace(
 'struct wr_iot_driver_owner wr_iot_driver_owner;',
 'struct wr_iot_driver_owner wr_iot_driver_owner;struct wr_ra2_assoc_owner wr_ra2_assoc_owner;')
cases=rekey['CASES'];anchor=' /* A refused tick retains countdown.'
assert cases.count(anchor)==1
cases=cases.replace(anchor,''' /* Association admitted first excludes the complete periodic key change. */
 reset(&ad);ad.wr_ra2_assoc_owner.associations=1;
 ad.ApCfg.MBSSID[2].REKEYCOUNTER=100;ad.ApCfg.MBSSID[2].StaCount=1;
 GREKEYPeriodicExec(NULL,&ad,NULL,&ad.ApCfg.MBSSID[2].REKEYTimer);
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 assert(!randoms&&!handshakes&&!installs&&!ad.wr_iot_control_users);
 assert(ad.wr_ra2_assoc_owner.associations==1&&!ad.wr_ra2_assoc_owner.key_active);
 assert(ad.ApCfg.MBSSID[2].REKEYCOUNTER==100);
#endif
'''+anchor)
control=(here/'mcu-control-admission.inc').read_text()
units=[('request',prefix+actors+ns['helpers']+main),
 ('periodic',timer_prefix+control+native.replace('VOID GREKEYPeriodicExec(',
  'VOID native_GREKEYPeriodicExec(',1)+'\n'+wrapped+cases)]
with tempfile.TemporaryDirectory(prefix='wr-ra2-key-arb-') as temp:
 d=Path(temp);(d/'ra2-gtk-request-kernel.h').write_text(request)
 for name,unit in units:
  (d/(name+'.c')).write_text(unit)
  for flags in ([],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT']):
   subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,'-I'+str(here),str(d/(name+'.c')),'-o',str(d/name)],check=True)
   subprocess.run([str(d/name)],check=True)
print('Both GTK writer paths share association arbitration: host PASS; integration pending')
