#!/usr/bin/env python3
"""Extract whole checked deletion for control-flow tests with synthetic MMIO/layout."""
import argparse
import re
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'hw_ctrl/cmm_asic_mt.c').read_text()
start=s.index('INT wr_iot_delete_wcid_checked(');end=s.index('\n}',start)+2;body=s[start:end]
unions=''
for number in [0,3,4]:
    fields=sorted(set(re.findall(r'dw'+str(number)+r'->field\.(\w+)',body)))
    unions+=('union WTBL_1_DW%d {unsigned int word;struct {'%number
             + ''.join('unsigned int %s:1;'%f for f in fields)+'} field;};\n')
prefix=r'''
#include <assert.h>
#include <string.h>
#define FALSE 0
#define WCID_ALL 255
#define MCAST_WCID 0
#define RT_DEBUG_TRACE 0
#define RT_DEBUG_ERROR 0
#define WR_IOT_WCID_APPLIED 0
#define WR_IOT_WCID_NOT_WRITTEN -1
#define WR_IOT_WCID_PARTIAL -2
#define WTBL1OR 1
#define WTBL_OFF_WIUCR 2
#define IU_BUSY 1
#define PSM_W_FLAG 2
#define WLAN_IDX_MASK 0xff00
#define WLAN_IDX(v) ((unsigned int)(v)<<8)
#define RX_CNT_CLEAR 4
#define TX_CNT_CLEAR 8
#define ADM_CNT_CLEAR 16
#define DBGPRINT(l,args) do{(void)(l);}while(0)
typedef unsigned char UCHAR;typedef unsigned int UINT32;typedef int INT;
typedef struct {int IndirectUpdateLock;struct {unsigned char wtbl_entry_cnt[4];} mac_ctrl;} RTMP_ADAPTER;
'''
layout=r'''
union fake_reg {unsigned int word,pn_0;struct {unsigned int pn_32:1;} field;};
struct wtbl_entry {
 struct {union WTBL_1_DW0 wtbl_1_d0;union fake_reg wtbl_1_d1,wtbl_1_d2;
 union WTBL_1_DW3 wtbl_1_d3;union WTBL_1_DW4 wtbl_1_d4;} wtbl_1;
 struct {union fake_reg wtbl_2_d0,wtbl_2_d1,wtbl_2_d15;} wtbl_2;
 unsigned int wtbl_addr[4],wtbl_fid[4],wtbl_eid[4];
};
static int held,acquired,released,writes,lookups,fail_lookup,commands,fail_command,delays,corrupt_address,initial_busy_lookup;
#define NdisZeroMemory(p,n) memset((p),0,(n))
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;acquired++;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;released++;}while(0)
#define RtmpusecDelay(n) do{assert((n)==50);delays++;}while(0)
static int mt_wtbl_get_entry234(RTMP_ADAPTER *a,UCHAR c,struct wtbl_entry *e){
 (void)a;(void)c;lookups++;if(lookups==fail_lookup)return 0;
 for(int i=0;i<4;i++){e->wtbl_addr[i]=100+(unsigned int)i*100;}
 return 1;
}
static void write_reg(unsigned int reg,unsigned int v){
#ifdef RTMP_PCI_SUPPORT
 assert(held);
#endif
 (void)v;writes++;if(reg==WTBL_OFF_WIUCR)commands++;}
static unsigned int read_reg(unsigned int reg){if(reg==100&&corrupt_address==1)return 1; if(reg==104&&corrupt_address==2)return 1; return reg==WTBL_OFF_WIUCR&&(commands==fail_command||lookups==initial_busy_lookup)?IU_BUSY:0;}
#define RTMP_IO_WRITE32(a,r,v) do{(void)(a);write_reg((r),(v));}while(0)
#define RTMP_IO_READ32(a,r,v) do{(void)(a);*(v)=read_reg(r);}while(0)
static void reset(void){held=acquired=released=writes=lookups=commands=delays=0;fail_lookup=fail_command=initial_busy_lookup=-1;corrupt_address=0;}
'''
suffix=r'''
int main(void){RTMP_ADAPTER a={0};a.mac_ctrl.wtbl_entry_cnt[0]=4;
reset();fail_lookup=1;assert(wr_iot_delete_wcid_checked(&a,3)==-1&&!writes&&!held);
reset();initial_busy_lookup=1;assert(wr_iot_delete_wcid_checked(&a,3)==-1&&!writes&&!commands&&!delays&&!held&&acquired==released);
reset();initial_busy_lookup=2;assert(wr_iot_delete_wcid_checked(&a,WCID_ALL)==-2);
assert(lookups==2&&commands==3&&!held&&acquired==released);
for(int stage=1;stage<=3;stage++){
 reset();fail_command=stage;assert(wr_iot_delete_wcid_checked(&a,3)==-2);
 assert(writes>0&&delays==100&&!held&&acquired==released);
}
for(int word=1;word<=2;word++){
 reset();corrupt_address=word;assert(wr_iot_delete_wcid_checked(&a,3)==-2);
 assert(!held&&acquired==released&&commands==3);
}
reset();assert(wr_iot_delete_wcid_checked(&a,3)==0&&lookups==1&&commands==3&&!held);
reset();fail_lookup=2;assert(wr_iot_delete_wcid_checked(&a,WCID_ALL)==-2);
assert(lookups==2&&commands==3&&writes>0&&!held);
reset();assert(wr_iot_delete_wcid_checked(&a,WCID_ALL)==0);
assert(lookups==4&&commands==4*3&&!held&&acquired==released);
reset();assert(wr_iot_delete_wcid_checked(&a,4)==-1&&!lookups&&!writes);
reset();a.mac_ctrl.wtbl_entry_cnt[0]=0;
assert(wr_iot_delete_wcid_checked(&a,WCID_ALL)==-1&&!lookups&&!writes);
a.mac_ctrl.wtbl_entry_cnt[0]=255;reset();
assert(wr_iot_delete_wcid_checked(&a,WCID_ALL)==0&&lookups==255&&commands==765&&!held);
return 0;}
'''
a.output.write_text(prefix+unions+layout+body+suffix,encoding='utf-8')
print('Extracted full deletion; fake layout/MMIO checks control flow only')
