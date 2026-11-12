#!/usr/bin/env python3
"""Exercise the experimental branch extracted from a checked TXD constructor."""
import argparse
from pathlib import Path
import runpy
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path, help='checked candidate mac/mt_mac.c')
a = p.parse_args()
here = Path(__file__).resolve().parent
policy = runpy.run_path(str(here / 'ra2-beacon-no-host-status.py'))
original = a.source.read_text()
changed = policy['compose'](original)
assert changed.replace('if (' + policy['POLICY'] + ' &&\n                    (' +
                       policy['ANCHOR'][4:-1] + '))', policy['ANCHOR'], 1) == original
for invalid in (changed, original.replace(policy['ANCHOR'], 'if (0)')):
    try:
        policy['compose'](invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('Changed/already composed constructor accepted')


def block_end(text, start):
    opening = text.index('{', start)
    depth = 1
    for i in range(opening + 1, len(text)):
        depth += (text[i] == '{') - (text[i] == '}')
        if not depth:
            return i + 1
    raise ValueError('Unclosed branch')


start = changed.index('if (' + policy['POLICY'])
end = block_end(changed, start)
assert changed[end:].lstrip().startswith('else')
end = block_end(changed, end)
branch = changed[start:end]
prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef uint8_t UINT8;
typedef uint32_t UINT32;
#define IS_MT7603(ad) ((ad)->mt)
#define Q_IDX_BCN 7
#define FC_TYPE_MGMT 0
#define SUBTYPE_BEACON 8
static int calls,fail;
static int allocate(UINT8 *pid,UINT32 *generation)
{ calls++; if(fail)return -1;*pid=23;*generation=42;return 0; }
#define AddTxSStatus(...) allocate(&status_pid,&status_generation)
static void exercise(int fault)
{
 struct {int mt;struct {int BssidNum;} ApCfg;} ad={1,{3}},*pAd=&ad;
 struct {int bss_idx,TxSPriv;UINT32 TxSReservationGeneration;UINT8 TxSReservationPid;}
  metadata={2,2,0,0},*info=&metadata;
 struct {int q_idx;} queue={7},*txd_0=&queue;
 struct {int frm_type,sub_type;} frame={0,8},*txd_2=&frame;
 struct {int pid,tx_status_2_host;} status={0,1},*txd_5=&status;
 struct {unsigned TxS2HostStatusPerPktType[4];} ctl={{~0U,~0U,~0U,~0U}},*TxSCtl=&ctl;
 calls=fail=0;
 switch(fault){
 case 1:info->bss_idx=info->TxSPriv=0;break;
 case 2:info->bss_idx=info->TxSPriv=1;break;
 case 3:info->TxSPriv=1;break;
 case 4:txd_0->q_idx=0;break;
 case 5:txd_2->frm_type=2;break;
 case 6:txd_2->sub_type=4;break;
 case 7:ad.mt=0;break;
 case 8:ad.ApCfg.BssidNum=4;break;
 case 9:info->bss_idx=info->TxSPriv=0;fail=1;break;
 case 10:info->bss_idx=info->TxSPriv=0;ctl.TxS2HostStatusPerPktType[0]=0;break;
 }
'''
tail = r'''
 assert(calls==(fault>0&&fault<10));
 assert(txd_5->tx_status_2_host==(fault>0&&fault<9));
 assert(info->TxSReservationGeneration==(fault>0&&fault<9?42U:0U));
 assert(info->TxSReservationPid==(fault>0&&fault<9?23U:0U));
}
int main(void)
{
 for(int repeat=0;repeat<300;repeat++)for(int fault=0;fault<11;fault++)exercise(fault);
 puts("PASS unbound ra2 long-beacon policy: zero PID allocation, Main/Guest unchanged, scope mismatches and allocation failure; no pacing/RF proof");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-no-host-status-') as scratch:
    src = Path(scratch) / 'test.c'
    exe = Path(scratch) / 'test'
    src.write_text(prefix + branch + tail)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    str(src), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
