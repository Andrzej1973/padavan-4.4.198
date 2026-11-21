#!/usr/bin/env python3
"""Execute generated dispatch envelope with injected command body and cleanup."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
text=(a.candidate/'common/rtmp_init.c').read_text();start=text.index('VOID CMDHandler(')
body=text[start:text.index('\n#endif /* RTMP_MAC_PCI */',start)]
assert body.count('wr_iot_control_enter(pAd)')==1
assert body.count('wr_iot_control_leave(pAd)')==1
start=body.index('if(!(RTMP_TEST_FLAG')
condition=body[start:body.index('\n\t\t{',start)]
start=body.index(' if(wr_iot_command_admitted)')
start=body.rfind('#if',0,start)
tail=body[start:body.index('\n\t\tif (cmdqelmt->CmdFromNdis',start)]
prefix=r'''
#include <assert.h>
#include <stdio.h>
typedef struct {int mt;unsigned flags;} RTMP_ADAPTER;
typedef struct {int command;} CMD;
#define IS_MT7603(ad) ((ad)->mt)
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 2
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
#define CMDTHREAD_MLME_PERIOIDC_EXEC 7
static int entered,left,active,allowed,dispatched,cleaned,reset;
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
static int wr_iot_control_enter(RTMP_ADAPTER *ad){assert(ad);entered++;if(!allowed)return 0;active++;return 1;}
static void wr_iot_control_leave(RTMP_ADAPTER *ad){assert(ad&&active);left++;active--;}
#endif
#if defined(MT7603) && defined(DMA_RESET_SUPPORT)
static void wr_iot_radio_reset_drain(RTMP_ADAPTER *ad){assert(ad&&!active);reset++;}
#endif
static void wr_iot_queue_cleanup(CMD *cmd){assert(cmd&&!active);cleaned++;}
static void dispatch(RTMP_ADAPTER *pAd,CMD *cmdqelmt){
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
int wr_iot_command_admitted=0;
#endif
'''
main=r'''
}
int main(void){RTMP_ADAPTER ad;CMD cmd;unsigned flags;int mt,periodic;
for(mt=0;mt<2;mt++)for(flags=0;flags<4;flags++)for(allowed=0;allowed<2;allowed++)for(periodic=0;periodic<2;periodic++){
 ad.mt=mt;ad.flags=flags;cmd.command=periodic?7:9;entered=left=active=dispatched=cleaned=reset=0;
 dispatch(&ad,&cmd);assert(cleaned==1&&!active);
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 assert(dispatched==(!flags&&(!mt||allowed)));assert(entered==(!flags&&mt));assert(left==(!flags&&mt&&allowed));
#else
 assert(dispatched==!flags);assert(!entered&&!left);
#endif
#if defined(MT7603) && defined(DMA_RESET_SUPPORT)
 assert(reset==(periodic&&!flags));
#else
 assert(!reset);
#endif
}puts("PASS generated command envelope: admitted/denied/other-chip/NIC/halt, cleanup exactly once, reset after release including denied periodic; body/cleanup/locks injected");}
'''
with tempfile.TemporaryDirectory(prefix='wr-command-admission-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+condition+'\n{dispatched++;}\n'+tail+main)
 for flags in ([],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT'],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT','-DDMA_RESET_SUPPORT']):
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,str(c),'-o',td+'/check'],check=True)
  subprocess.run([td+'/check'],check=True)
