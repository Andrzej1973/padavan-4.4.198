#!/usr/bin/env python3
"""Extract moved MCS/rate helper; MCS implementation remains injected."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'ap/ap_wds.c').read_text()
start=s.index('static VOID wr_iot_wds_finish_peer(');end=s.index('\n}',start)+2
body=s[start:end]
prefix=r'''
#include <assert.h>
#include <stddef.h>
#define VOID void
typedef unsigned int UINT;
typedef struct {int SupportRateMode;} MAC_TABLE_ENTRY;
typedef struct {struct {int PhyMode;} wdev;} RT_802_11_WDS_ENTRY;
typedef struct {struct {RT_802_11_WDS_ENTRY WdsEntry[1];} WdsTab;struct {int PhyMode;} CommonCfg;} RTMP_ADAPTER;
#define MODE_OFDM 1
#define MODE_CCK 2
#define MODE_HTMIX 3
#define MODE_HTGREENFIELD 4
#define SUPPORT_OFDM_MODE 1
#define SUPPORT_CCK_MODE 2
#define SUPPORT_HT_MODE 4
#define WMODE_CAP_2G(m) ((m)&1)
static int mcs,lease=1;
#define RTMPSetSupportMCS(...) do{assert(lease);mcs++;}while(0)
'''
suffix=r'''
int main(void){RTMP_ADAPTER a={0};MAC_TABLE_ENTRY e={99};
wr_iot_wds_finish_peer(&a,&e,0,0);assert(!mcs&&e.SupportRateMode==99);
wr_iot_wds_finish_peer(&a,NULL,0,2);assert(!mcs);
wr_iot_wds_finish_peer(&a,&e,0,1);assert(mcs==1&&e.SupportRateMode==99);
int modes[]={255,MODE_OFDM,MODE_CCK,MODE_HTMIX,MODE_HTGREENFIELD,42};
for(int band=0;band<2;band++)for(int i=0;i<6;i++){
 e.SupportRateMode=99;a.CommonCfg.PhyMode=band;a.WdsTab.WdsEntry[0].wdev.PhyMode=modes[i];
 int before=mcs;wr_iot_wds_finish_peer(&a,&e,0,2);assert(mcs==before+1);
 int expected=99;
 if(i<2)expected=SUPPORT_OFDM_MODE|(band?SUPPORT_CCK_MODE:0);
 if(i==2)expected=SUPPORT_CCK_MODE;
#ifdef DOT11_N_SUPPORT
 if(i==3||i==4)expected=SUPPORT_HT_MODE|SUPPORT_OFDM_MODE|(band?SUPPORT_CCK_MODE:0);
#endif
 assert(e.SupportRateMode==expected);
}
return 0;}
'''
a.output.write_text(prefix+body+suffix,encoding='utf-8')
print('Extracted actual rate helper; RTMPSetSupportMCS call injected, not RF tested')
