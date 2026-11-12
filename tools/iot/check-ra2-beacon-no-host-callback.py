#!/usr/bin/env python3
"""Execute actual callback composition; this does not test PID/parser aliasing."""
import argparse
import ast
from pathlib import Path
import runpy
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('driver', type=Path)
a = p.parse_args()
here = Path(__file__).resolve().parent
compose = runpy.run_path(str(here / 'ra2-beacon-no-host-status.py'))['compose_callback']
source = compose((a.driver / 'tx_rx/txs.c').read_text())
try:
    compose(source)
except ValueError:
    pass
else:
    raise AssertionError('Repeated callback composition accepted')
signature = 'INT32 BcnTxSHandler(RTMP_ADAPTER *pAd, CHAR *Data, UINT32 Priv)'
start = source.index(signature)
body = source[start:source.index('\n}', start) + 2]
tree = ast.parse((here / 'check-beacon-txs-stop.py').read_text())
prefixes = [ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'pre' for t in n.targets)]
assert len(prefixes) == 1
prefix = prefixes[0].replace('int OpMode,BcnRingLock;', 'int chip,OpMode,BcnRingLock;')
prefix += '\n#define MT7603 1\n#define IS_MT7603(ad) ((ad)->chip==0x7603)\n'
tail = r'''
int main(void){
 for(int chip=0;chip<2;chip++)for(unsigned bss=0;bss<3;bss++){
  RTMP_ADAPTER ad={.chip=chip?0x7603:0,.OpMode=OPMODE_AP,.ApCfg.BssidNum=3};
  TXS_STRUC report={.txs_d1.timestamp=123,.txs_d4.sn=321};
  ad.ApCfg.MBSSID[bss]=(BSS_STRUCT){.bcn_buf.bcn_state=BCN_TX_STOP,.bcn_not_idle_time=9,.timer_loop=2};
  BSS_STRUCT before=ad.ApCfg.MBSSID[bss];
  assert(BcnTxSHandler(&ad,(CHAR *)&report,bss)==-1&&!ad.BcnRingLock);
  assert(!memcmp(&before,&ad.ApCfg.MBSSID[bss],sizeof(before)));
  ad.ApCfg.MBSSID[bss].bcn_buf.bcn_state=1;before=ad.ApCfg.MBSSID[bss];
  if(chip&&bss==2){
   for(int duplicate=0;duplicate<3;duplicate++){
    assert(BcnTxSHandler(&ad,(CHAR *)&report,bss)==-1&&!ad.BcnRingLock);
    assert(!memcmp(&before,&ad.ApCfg.MBSSID[bss],sizeof(before)));
   }
  }else{
   assert(!BcnTxSHandler(&ad,(CHAR *)&report,bss)&&!ad.BcnRingLock);
   assert(ad.ApCfg.MBSSID[bss].bcn_buf.bcn_state==BCN_TX_IDLE);
   assert(ad.ApCfg.MBSSID[bss].timer_loop==3&&!ad.ApCfg.MBSSID[bss].bcn_not_idle_time);
  }
  assert(BcnTxSHandler(&ad,(CHAR *)&report,3)==-1&&!ad.BcnRingLock);
 }
 puts("PASS actual unbound callback: ra2 state/timestamp slot unchanged across duplicate reports; Main/Guest/other chip and STOP/bounds preserved. No PID alias or cold-epoch proof");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-no-host-callback-') as scratch:
    src = Path(scratch) / 'test.c'
    exe = Path(scratch) / 'test'
    src.write_text(prefix + body + tail)
    for extra in ([], ['-DDBG']):
        subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-variable', '-fsanitize=address,undefined',
                        '-fno-pie', '-no-pie', str(src), '-o', str(exe)] + extra, check=True)
        subprocess.run([str(exe)], check=True)
