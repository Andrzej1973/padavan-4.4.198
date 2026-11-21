#!/usr/bin/env python3
"""Execute composed response length/copy statements with pinned SDK types."""
import argparse
from pathlib import Path
import runpy
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args()
here=Path(__file__).resolve().parent
api=runpy.run_path(str(here/'ft-r1kh-snapshot-composition.py'))
names=('common/cmm_wpa.c','ap/ap_ftkd.c')
sources={name:(a.source/name).read_text(encoding='latin1') for name in names}
response=api['compose_related'](sources)['ap/ap_ftkd.c']
start=response.index('VOID TYPE_FUNC FT_KDP_KeyResponseToUs(')
response=response[start:response.index('\n}',start)+2]
guard=response[response.index('if (!pInfo || InfoLen < 0'):]
guard=guard[:guard.index(';')+1]
copy=response[response.index('NdisMoveMemory(&wr_owned_response,'):]
copy=copy[:copy.index('return;')+len('return;')]
header=(a.source/'include/ft.h').read_text()
def native_type(tag,tail):
    start=header.index(tag)
    return header[start:header.index(tail,start)+len(tail)]
types=native_type('typedef struct GNU_PACKED _FT_KDP_PMK_KEY_INFO {','} FT_KDP_PMK_KEY_INFO;')
types+='\n'+native_type('typedef struct GNU_PACKED _FT_KDP_EVT_KEY_ELM','} FT_KDP_EVT_KEY_ELM;')
prefix=r'''
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef unsigned char UCHAR;
typedef uint16_t UINT16;
typedef uint32_t UINT32;
typedef int32_t INT32;
#define GNU_PACKED __attribute__((packed))
#define ETH_ALEN 6
#define FT_IP_ADDRESS_SIZE 4
#define FT_NONCE_SIZE 8
#define FT_KDP_R0KHID_MAX_SIZE 48
#define FT_KDP_WPA_NAME_MAX_SIZE 16
#define FT_KDP_R1KHID_MAX_SIZE 6
#define FT_KDP_S1KHID_MAX_SIZE 6
#define FT_KDP_PMKR1_MAX_SIZE 32
#define NdisMoveMemory(a,b,n) memcpy(a,b,n)
'''
probe=r'''
static int accepted;
static FT_KDP_EVT_KEY_ELM result;
static void parse(UCHAR *pInfo,INT32 InfoLen){
 FT_KDP_EVT_KEY_ELM wr_owned_response,*pEvtKeyRsp;
 UCHAR *pNonce;
'''+guard+r'''
 pNonce=pInfo+FT_IP_ADDRESS_SIZE;
'''+copy+r'''
 result=*pEvtKeyRsp;accepted++;
}
'''
main=r'''
int main(void){
 size_t needed=FT_IP_ADDRESS_SIZE+FT_NONCE_SIZE+sizeof(FT_KDP_EVT_KEY_ELM);
 for(size_t n=0;n<needed;n++){
  UCHAR *short_input=malloc(n?n:1);assert(short_input);
  memset(short_input,0,n);parse(short_input,(INT32)n);free(short_input);
  assert(!accepted);
 }
 parse(NULL,(INT32)needed);parse(NULL,-1);assert(!accepted);
 UCHAR *input=calloc(1,needed);assert(input);
 parse(input,-1);assert(!accepted);
 FT_KDP_EVT_KEY_ELM value={0};value.KeyInfo.R0KHIDLen=48;
 value.PMKR1[0]=42;
 memcpy(input+FT_IP_ADDRESS_SIZE+FT_NONCE_SIZE,&value,sizeof(value));
 parse(input,(INT32)needed);assert(accepted==1&&result.PMKR1[0]==42);
 memset(input,0,needed);assert(result.PMKR1[0]==42);
 value.KeyInfo.R0KHIDLen=49;
 memcpy(input+FT_IP_ADDRESS_SIZE+FT_NONCE_SIZE,&value,sizeof(value));
 parse(input,(INT32)needed);assert(accepted==1);
 free(input);
 puts("PASS | FT IAPP response copy | all short lengths, null/negative refusal, exact size, R0KH bounds and owned copy");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-iapp-copy-') as td:
    source=Path(td)/'check.c';exe=Path(td)/'check'
    source.write_text(prefix+types+probe+main)
    subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',
      '-fsanitize=address,undefined','-fno-pie','-no-pie',str(source),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)

# Execute the complete composed handler; cache and completion dependencies are mocks.
actors=r'''
typedef void VOID;
typedef UCHAR *PUINT8;
typedef int BOOLEAN;
#define TYPE_FUNC
#define IN
#define TRUE 1
#define FALSE 0
#define LEN_PMK 32
#define RT_DEBUG_ERROR 0
#define RT_DEBUG_TRACE 0
#define DBGPRINT(level,args) do { if(0)printf args; } while(0)
#define MTWF_LOG(a,b,c,args) do { if(0)printf args; } while(0)
#define jiffies 0L
#define OS_HZ 100
#define RTMPEqualMemory(a,b,n) (!memcmp(a,b,n))
typedef struct {UCHAR PmkR1Key[32];} FT_R1HK_ENTRY,*PFT_R1HK_ENTRY;
typedef struct {int FT_R1kh_CacheMiss_Times,FT_R1kh_CacheMiss_Hard,wcid,ack_r1kh;} MAC_TABLE_ENTRY;
typedef struct {struct {struct {int FlgIsFtKdpInit;} FtTab;} ApCfg;} RTMP_ADAPTER,*PRTMP_ADAPTER;
static MAC_TABLE_ENTRY peer;
static int hit,store_fail,stores,acks,cache_reads,peer_reads;
static UCHAR saved_key[32];
#define RTMP_OS_COMPLETE(p) do {(void)(p);acks++;}while(0)
#define IAPP_DAEMON_CMD_PARSE(info,len,ip,data,size) \
 do {memcpy(&(ip),(info),4);(data)=(info)+4;(size)=(len)-4;(void)(ip);(void)(size);}while(0)
static int wr_ft_r1kh_snapshot(RTMP_ADAPTER *ad,UCHAR *name,FT_R1HK_ENTRY *out){
 (void)ad;(void)name;cache_reads++;memcpy(out->PmkR1Key,saved_key,32);return hit;
}
static MAC_TABLE_ENTRY *MacTableLookup(RTMP_ADAPTER *ad,UCHAR *mac){(void)ad;(void)mac;peer_reads++;return &peer;}
static int FT_R1khEntryInsert(RTMP_ADAPTER *ad,UCHAR *r0,UCHAR *name,UCHAR *key,
 UCHAR *cipher,UCHAR *akm,UINT32 life,UINT32 deadline,UCHAR *id,UCHAR len,UCHAR *mac){
 (void)ad;(void)r0;(void)name;(void)cipher;(void)akm;(void)life;(void)deadline;(void)id;(void)len;(void)mac;
 stores++;if(store_fail)return -1;memcpy(saved_key,key,32);hit=1;return 0;
}
'''
handler_main=r'''
int main(void){
 RTMP_ADAPTER ad={0};ad.ApCfg.FtTab.FlgIsFtKdpInit=1;
 size_t needed=12+sizeof(FT_KDP_EVT_KEY_ELM);
 UCHAR *input=calloc(1,needed);assert(input);
 FT_KDP_EVT_KEY_ELM value={0};value.ElmId=FT_KDP_ELM_ID_PRI;value.ElmLen=FT_KDP_ELM_PRI_LEN;
 value.OUI[0]=FT_KDP_ELM_PRI_OUI_0;value.OUI[1]=FT_KDP_ELM_PRI_OUI_1;value.OUI[2]=FT_KDP_ELM_PRI_OUI_2;
 value.PMKR1[0]=42;memcpy(input+12,&value,sizeof(value));
 for(size_t n=0;n<needed;n++){
  UCHAR *short_input=calloc(1,n?n:1);assert(short_input);
  FT_KDP_KeyResponseToUs(&ad,short_input,(INT32)n);free(short_input);
 }
 FT_KDP_KeyResponseToUs(&ad,NULL,(INT32)needed);
 FT_KDP_KeyResponseToUs(&ad,input,-1);
 value.OUI[1]^=1;memcpy(input+12,&value,sizeof(value));
 FT_KDP_KeyResponseToUs(&ad,input,(INT32)needed);
 value.OUI[1]^=1;value.KeyInfo.R0KHIDLen=49;
 memcpy(input+12,&value,sizeof(value));
 FT_KDP_KeyResponseToUs(&ad,input,(INT32)needed);
 value.KeyInfo.R0KHIDLen=48;value.ElmLen=FT_KDP_ELM_PRI_LEN-1;
 memcpy(input+12,&value,sizeof(value));
 FT_KDP_KeyResponseToUs(&ad,input,(INT32)needed);
 value.ElmLen=FT_KDP_ELM_PRI_LEN+1;memcpy(input+12,&value,sizeof(value));
 FT_KDP_KeyResponseToUs(&ad,input,(INT32)needed);
 value.ElmLen=FT_KDP_ELM_PRI_LEN;memcpy(input+12,&value,sizeof(value));
 ad.ApCfg.FtTab.FlgIsFtKdpInit=0;
 FT_KDP_KeyResponseToUs(&ad,input,(INT32)needed);
 ad.ApCfg.FtTab.FlgIsFtKdpInit=1;
 assert(!cache_reads&&!peer_reads&&!stores&&!acks);

 peer.FT_R1kh_CacheMiss_Times=1;peer.FT_R1kh_CacheMiss_Hard=1;
 store_fail=1;FT_KDP_KeyResponseToUs(&ad,input,(INT32)needed);
 assert(stores==1&&!acks&&peer.FT_R1kh_CacheMiss_Times==1&&peer.FT_R1kh_CacheMiss_Hard==1);
 store_fail=0;FT_KDP_KeyResponseToUs(&ad,input,(INT32)needed);
 assert(stores==2&&saved_key[0]==42&&!peer.FT_R1kh_CacheMiss_Times);
#ifdef R1KH_HARD_RETRY
 assert(acks==1&&!peer.FT_R1kh_CacheMiss_Hard);
#else
 assert(!acks);
#endif
 /* Record existing same-key behavior; identity-bound ACK integration is pending. */
 peer.FT_R1kh_CacheMiss_Times=1;
 FT_KDP_KeyResponseToUs(&ad,input,(INT32)needed);
 assert(stores==2&&peer.FT_R1kh_CacheMiss_Times==1);
 free(input);
 puts("PASS | complete prepared IAPP handler | failed store retains retry state; malformed/inactive inputs have no cache/peer side effects; store failure retains state; same-key bypass reproduced");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-iapp-handler-') as td:
    source=Path(td)/'check.c';exe=Path(td)/'check'
    source.write_text(prefix+types+actors+response+handler_main)
    for flags in ([],['-DR1KH_HARD_RETRY']):
        subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',
          '-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,str(source),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
