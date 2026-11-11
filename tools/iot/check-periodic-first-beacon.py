#!/usr/bin/env python3
"""Join generated periodic wrapper/admission with the bounded OPEN wait fixture."""
import argparse
import ast
from pathlib import Path
import subprocess
import tempfile

here = Path(__file__).resolve().parent
header = (here / 'beacon-producer-kernel.h').read_text()
for node in ast.parse((here / 'prepare-driver-api.py').read_text()).body:
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        continue
    call = node.value
    if not isinstance(call.func, ast.Name) or call.func.id != 'one':
        continue
    if not isinstance(call.args[0], ast.Constant):
        continue
    if ast.literal_eval(call.args[0]) != 'include/wr-iot-beacon-producer-kernel.h':
        continue
    old, new = map(ast.literal_eval, call.args[1:])
    assert header.count(old) == 1
    header = header.replace(old, new, 1)
# Reproduce the exact capture hook installed by first-beacon composition.
old = '      wr_iot_beacon_gate_begin(gate, gate->generation, ticket);'
new = old + '\n if (ok && protect) wr_iot_first_beacon_capture_locked(ad,bss,ticket->generation);'
assert header.count(old) == 1
header = header.replace(old, new, 1)
wrapper_tree = ast.parse((here / 'prepare-beacon-producer-candidate.py').read_text())
wrappers = [ast.literal_eval(node.value) for node in ast.walk(wrapper_tree)
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
            and target.id == 'beacon_wrapper' for target in node.targets)]
assert len(wrappers) == 1
wrapper = wrappers[0]
api_tree = ast.parse((here / 'prepare-driver-api.py').read_text())
periodic_edits = [node.value for node in api_tree.body
                  if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                  and isinstance(node.value.func, ast.Name) and node.value.func.id == 'one'
                  and isinstance(node.value.args[0], ast.Constant)
                  and node.value.args[0].value == 'ap/ap_connect.c']
assert len(periodic_edits) == 1
old, new = map(ast.literal_eval, periodic_edits[0].args[1:])
assert wrapper.count(old) == 1
wrapper = wrapper.replace(old, new, 1)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('driver', nargs='?', type=Path)
args = parser.parse_args()
if args.driver:
    final_header = (args.driver / 'include/wr-iot-beacon-producer-kernel.h').read_text()
    assert header in final_header
    final_source = (args.driver / 'ap/ap_connect.c').read_text()
    assert final_source.count(wrapper.strip()) == 1
fixture = (here / 'check-precreated-first-beacon-wait.c').read_text()
# Inline only the shared ABI fixture to extend its synthetic adapter layout.
owner = (here / 'check-driver-api-owner-binding.c').read_text()
owner = owner.replace('struct {struct {PNET_DEV if_dev;} wdev;} MBSSID[3];',
                      'struct {struct {PNET_DEV if_dev;} wdev;struct {int bcn_state,bBcnSntReq;} bcn_buf;} MBSSID[3];')
owner = owner.replace('unsigned BssidNum;', 'unsigned char BssidNum;')
fixture = fixture.replace('#include "check-driver-api-owner-binding.c"', owner)
extra = r'''
#undef WDEV_NUM_MAX
#define WDEV_NUM_MAX 3
#define RTMP_MAC_PCI 1
#define VOID void
typedef unsigned int UINT32;
#define BCN_TX_IDLE 0
#define READ_ONCE(x) (x)
static int builders,txs_reads;
static int WrBeaconDmaOutstanding(RTMP_ADAPTER *ad,unsigned int bss)
{assert(bss==2&&!ad->BcnRingLock);return 0;}
static int WrBeaconTxSOutstanding(RTMP_ADAPTER *ad,unsigned int bss)
{
 assert(bss==2&&!ad->BcnRingLock);
 txs_reads++;
 if(mode==12 || (mode==16&&txs_reads==1))return 1;
 if(mode==13 || (mode==17&&txs_reads==1))return -1;
 return 0;
}
static void wr_iot_APUpdateBeaconFrame_inner(RTMP_ADAPTER *ad,INT bss)
{
 assert(bss==2&&!ad->BcnRingLock);builders++;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 if(mode==3)assert(wr_iot_first_beacon_expire(&ad->wr_iot_first_beacon,&ad->wr_iot_first_beacon.identity));
 if(mode==6)ad->wr_iot_first_beacon_capture.device=ad->net_dev;
 if(mode!=1)wr_iot_first_beacon_published_locked(ad,2);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
}
'''
# Include the real wait before its admission helpers, so its kernel capture is declared.
anchor = '#include "precreated-first-beacon-wait.inc"'
assert fixture.count(anchor) == 1
fixture = fixture.replace(anchor, anchor + '\n' + extra + '\n' + header + '\n' + wrapper, 1)
start = fixture.index(' assert(wr_iot_beacon_gate_begin(&ad->wr_iot_beacon_gates[2],7,&pin));')
end = fixture.index(' if(mode==2)ad->wr_iot_transition.main_ready=0;', start)
fixture = fixture[:start] + '''
 if(mode==14)ad->ApCfg.MBSSID[2].bcn_buf.bcn_state=1;
 if(mode==15)assert(wr_iot_beacon_gate_revoke(&ad->wr_iot_beacon_gates[2],7));
 APUpdateBeaconFrame(ad,2);
 if(mode>=16){
  assert(!builders&&!ad->wr_iot_first_beacon.submitted);
  assert(!ad->wr_iot_beacon_gates[2].active);
  APUpdateBeaconFrame(ad,2);
 }
 assert(builders==(mode>=12&&mode<16?0:1));
''' + fixture[end:]
fixture = fixture.replace(' struct wr_iot_beacon_producer_ticket pin={0};\n', '')
fixture = fixture.replace(' assert(wr_iot_beacon_gate_end(&ad->wr_iot_beacon_gates[2],&pin)||(mode==5));\n', '')
fixture = fixture.replace(' RTMP_SEM_UNLOCK(&ad->BcnRingLock);\n}\nint main', '}\nint main', 1)
fixture = fixture.replace('mode<12', 'mode<18').replace('opening=&ad;locked=1;wait_calls=0;', 'opening=&ad;locked=1;wait_calls=0;builders=txs_reads=0;')
fixture = fixture.replace('mode==0||mode==11', 'mode==0||mode==11||mode>=16')
with tempfile.TemporaryDirectory(prefix='wr-iot-periodic-first-') as scratch:
    root = Path(scratch)
    source, executable = root / 'check.c', root / 'check'
    source.write_text(fixture)
    subprocess.run(['gcc', '-std=gnu11', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I' + str(here), str(source), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
    size = sum(path.stat().st_size for path in root.iterdir())
assert not root.exists()
print('PASS generated periodic wrapper/admission + actual bounded OPEN wait with pending/unknown TxS, later progress, non-IDLE and revoked producer. Host scheduler/MMIO/submission injected. Scratch removed bytes', size)
