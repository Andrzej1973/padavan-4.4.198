#!/usr/bin/env python3
"""Extract complete checked WTBL update; inject synthetic layout/MMIO/queues."""
import argparse
import re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'hw_ctrl/cmm_asic_mt.c').read_text()
start=s.index('INT wr_iot_update_rx_wcid_checked(');end=s.index('\n}',start)+2;body=s[start:end]
unions=''
for n in range(5):
 fields=sorted(set(re.findall(r'dw'+str(n)+r'->field\.(\w+)',body)))
 unions+='union WTBL_1_DW%d {unsigned int word;struct {'%n+''.join('unsigned int '+f+';' for f in fields)+'} field;};\n'
prefix=r'''
#include <assert.h>
#include <string.h>
#define FALSE 0
#define MAIN_MBSSID 0
#define MCAST_WCID 0
#define APCLI_MCAST_WCID 2
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
#define WTBL2_UPDATE_FLAG 32
#define RX_CNT_CLEAR 4
#define TX_CNT_CLEAR 8
#define ADM_CNT_CLEAR 16
#define WTBL_CIPHER_NONE 0
#define WTBL_CIPHER_WEP_40 1
#define Ndis802_11WEPDisabled 0
#define Ndis802_11AuthModeShared 1
#define Ndis802_11AuthModeAutoSwitch 2
#define MMPS_DYNAMIC 1
#define AC_QUEUE_STOP 0
#define AC_QUEUE_START 1
#define IS_ENTRY_CLIENT(e) ((e)->type==1)
#define IS_ENTRY_APCLI(e) ((e)->type==2)
#define IS_HT_STA(e) ((e)->ht)
#define CLIENT_STATUS_TEST_FLAG(e,f) ((void)(e),(void)(f),0)
#define fCLIENT_STATUS_RDG_CAPABLE 1
#define DBGPRINT(l,args) do{(void)(l);}while(0)
typedef unsigned char UCHAR;typedef unsigned short USHORT;typedef unsigned int UINT32;typedef int INT;
struct wifi_dev {int hw_bssid_idx;};
typedef struct {int type,ht,func_tb_idx,WepStatus,AuthMode,MpduDensity,MaxRAmpduFactor,MmpsMode;struct wifi_dev *wdev;} MAC_TABLE_ENTRY;
struct rtmp_mac_ctrl {unsigned int wtbl_entry_cnt[4];};
typedef struct {int IndirectUpdateLock;struct rtmp_mac_ctrl mac_ctrl;struct {MAC_TABLE_ENTRY Content[4];} MacTab;} RTMP_ADAPTER;
'''
layout=r'''
union fake_reg {unsigned int word,pn_0;struct {unsigned int pn_32;} field;};
struct wtbl_entry {
 struct {union WTBL_1_DW0 wtbl_1_d0;union WTBL_1_DW1 wtbl_1_d1;union WTBL_1_DW2 wtbl_1_d2;
 union WTBL_1_DW3 wtbl_1_d3;union WTBL_1_DW4 wtbl_1_d4;} wtbl_1;
 struct {union fake_reg wtbl_2_d0,wtbl_2_d1,wtbl_2_d15;} wtbl_2;
 unsigned int wtbl_addr[4],wtbl_fid[4],wtbl_eid[4];
};
static int held,acquired,released,writes,commands,delays,stops,starts,initial_busy,fail_command,fail_lookup;
#define NdisZeroMemory(p,n) memset((p),0,(n))
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;acquired++;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;released++;}while(0)
#define RtmpusecDelay(n) do{assert((n)==50);delays++;}while(0)
static int mt_wtbl_get_entry234(RTMP_ADAPTER *a,USHORT c,struct wtbl_entry *e){
 (void)a;(void)c;if(fail_lookup)return 0;
 for(int i=0;i<4;i++){e->wtbl_addr[i]=100+(unsigned int)i*100;}
 return 1;
}
static void write_reg(unsigned int r,unsigned int v){
#ifdef RTMP_PCI_SUPPORT
 assert(held);
#endif
 (void)v;writes++;if(r==WTBL_OFF_WIUCR)commands++;
}
static unsigned int read_reg(unsigned int r){return r==WTBL_OFF_WIUCR&&(initial_busy||commands==fail_command)?IU_BUSY:0;}
#define RTMP_IO_WRITE32(a,r,v) do{(void)(a);write_reg((r),(v));}while(0)
#define RTMP_IO_READ32(a,r,v) do{(void)(a);*(v)=read_reg(r);}while(0)
static void MtAsicACQueue(RTMP_ADAPTER *a,int action,int index,unsigned int mask){
 (void)a;assert(index==0&&mask==15);
#ifdef RTMP_PCI_SUPPORT
 assert(held);
#endif
 if(action==AC_QUEUE_STOP)stops++;else {assert(action==AC_QUEUE_START&&stops==1&&!starts);starts++;}
}
static void reset(void){held=acquired=released=writes=commands=delays=stops=starts=initial_busy=fail_lookup=0;fail_command=-1;}
'''
suffix=r'''
int main(void){RTMP_ADAPTER a={0};struct wifi_dev w={0};UCHAR addr[6]={1,2,3,4,5,6};
a.mac_ctrl.wtbl_entry_cnt[0]=4;a.MacTab.Content[1].wdev=&w;a.MacTab.Content[1].type=1;
reset();initial_busy=1;assert(wr_iot_update_rx_wcid_checked(&a,1,addr)==-1&&!writes&&!commands&&!stops&&!starts&&!held&&acquired==released);
for(int stage=1;stage<=4;stage++){
 reset();fail_command=stage;assert(wr_iot_update_rx_wcid_checked(&a,1,addr)==-2);
 assert(writes>0&&delays==100&&stops==1&&starts==1&&!held&&acquired==released);
}
reset();assert(wr_iot_update_rx_wcid_checked(&a,1,addr)==0&&commands==4&&stops==1&&starts==1&&!held&&acquired==released);
reset();fail_lookup=1;assert(wr_iot_update_rx_wcid_checked(&a,1,addr)==-1&&!writes&&!stops&&!held);
reset();assert(wr_iot_update_rx_wcid_checked(&a,4,addr)==-1&&!writes&&!acquired);
reset();a.mac_ctrl.wtbl_entry_cnt[0]=0;assert(wr_iot_update_rx_wcid_checked(&a,1,addr)==-1&&!writes&&!acquired);
return 0;}
'''
a.output.write_text(prefix+unions+layout+body+suffix,encoding='utf-8')
print('Extracted complete checked WTBL update; synthetic layout and MMIO only')
