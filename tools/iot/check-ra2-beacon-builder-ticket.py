#!/usr/bin/env python3
"""Execute experimental ABI composition with the actual generated wrapper.

The large vendor inner body is injected here; final prepared driver/MIPS
compilation remains a separate gate before installing the experimental mode.
"""
import ast
from pathlib import Path
import runpy
import subprocess
import tempfile

here = Path(__file__).resolve().parent
tree = ast.parse((here / 'prepare-beacon-producer-candidate.py').read_text())
wrappers = [ast.literal_eval(n.value) for n in ast.walk(tree)
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and
            t.id == 'beacon_wrapper' for t in n.targets)]
assert len(wrappers) == 1
wrapper = wrappers[0]
api = ast.parse((here / 'prepare-driver-api.py').read_text())
for n in api.body:
    if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):
        call = n.value
        if (isinstance(call.func, ast.Name) and call.func.id == 'one' and
                isinstance(call.args[0], ast.Constant) and call.args[0].value == 'ap/ap_connect.c'):
            old, new = map(ast.literal_eval, call.args[1:])
            if 'wr_iot_APUpdateBeaconFrame_inner' in old:
                assert wrapper.count(old) == 1
                wrapper = wrapper.replace(old, new, 1)
queue = ast.parse((here / 'prepare-radio-queue-candidate.py').read_text())
prototypes = [ast.literal_eval(n.value) for n in queue.body
              if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and
              t.id == 'new_proto' for t in n.targets)]
assert len(prototypes) == 1
header = prototypes[0].split('} WR_BCN_TXS_RESERVATION;', 1)[0] + '} WR_BCN_TXS_RESERVATION;'
inner = '''static VOID wr_iot_APUpdateBeaconFrame_inner(RTMP_ADAPTER *pAd, INT apidx)
{
 WR_BCN_TXS_RESERVATION reservation={0};
 reservation.generation = write_tmac_info_beacon(pAd,apidx);
 submitted=reservation;calls++;
}
'''
compose = runpy.run_path(str(here / 'ra2-beacon-no-host-status.py'))['compose_builder_ticket']
source, header = compose(inner + wrapper, header)
try:
    compose(source, header)
except ValueError:
    pass
else:
    raise AssertionError('Repeated ABI composition accepted')
prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "beacon-producer-gate.h"
typedef uint8_t UINT8;typedef uint32_t UINT32;
typedef int INT;typedef void VOID;
typedef struct {struct {int BssidNum;} ApCfg;struct {int hif_type;} chipCap;} RTMP_ADAPTER;
#define MT_MAC 1
#define RTMP_MAC_PCI 1
#define HIF_MT 1
#define WDEV_NUM_MAX 3
static int calls,ends;
static int wr_iot_bcn_producer_begin(RTMP_ADAPTER *ad,int bss,struct wr_iot_beacon_producer_ticket *ticket)
{assert(ad&&bss>0);ticket->generation=17;ticket->active=1;return 1;}
static void wr_iot_bcn_producer_end(RTMP_ADAPTER *ad,int bss,struct wr_iot_beacon_producer_ticket *ticket)
{assert(ad&&bss>0&&ticket->active&&ticket->generation==17);ticket->active=0;ends++;}
static int wr_iot_bcn_periodic_ready(RTMP_ADAPTER *ad,int bss,struct wr_iot_beacon_producer_ticket *ticket)
{assert(ad&&bss>0&&ticket->active&&ticket->generation==17);return 1;}
static UINT32 write_tmac_info_beacon(RTMP_ADAPTER *ad,int bss){assert(ad&&bss>=0);return 0;}
'''
tail = r'''
int main(void){
 RTMP_ADAPTER ad={.ApCfg.BssidNum=3,.chipCap.hif_type=HIF_MT};
 APUpdateBeaconFrame(&ad,2);
 assert(calls==1&&ends==1&&submitted.producer.generation==17&&submitted.producer.active);
 APUpdateBeaconFrame(&ad,1);
 assert(calls==2&&ends==2&&submitted.producer.generation==17);
 APUpdateBeaconFrame(&ad,0);
 assert(calls==3&&ends==2&&!submitted.producer.active&&!submitted.producer.generation);
 APUpdateBeaconFrame(&ad,3);assert(calls==3&&ends==2);
 puts("PASS actual producer wrapper carries original ticket copy into internal reservation; Main NULL, Guest and early refusal preserved; inner body injected, no target proof");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-builder-ticket-') as scratch:
    src = Path(scratch) / 'test.c'
    exe = Path(scratch) / 'test'
    src.write_text(prefix + header + '\nstatic WR_BCN_TXS_RESERVATION submitted;\n' + source + tail)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I'+str(here), str(src), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
