#!/usr/bin/env python3
"""Compile/exercise factored vendor key bodies with actual payload/key layouts."""
import argparse,re,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
native=(a.source/'ap/ap_cfg.c').read_text()
base=runpy.run_path(str(here/'hostapd-key-copy-composition.py'))['compose'](native)
_,helpers,_=runpy.run_path(str(here/'hostapd-key-execution-composition.py'))['compose'](base)
oid=(a.source/'include/oid.h').read_text();wpa=(a.source/'include/wpa_cmm.h').read_text()
def structure(text,start,end):
 begin=text.index(start);return text[begin:text.index(end,begin)+len(end)]
layouts=structure(oid,'struct ieee80211req_key {','};')+'\n'+structure(oid,'struct ieee80211req_del_key {','};')+'\n'+structure(wpa,'typedef struct _CIPHER_KEY {','} CIPHER_KEY, *PCIPHER_KEY;')
prefix=r'''
#include <assert.h>
#include <string.h>
#include <stddef.h>
#include <stdio.h>
#include <stdarg.h>
typedef unsigned char UCHAR,UINT8;typedef unsigned short UINT16;
typedef unsigned long long UINT64;typedef unsigned int UINT;typedef int INT;
#define HOSTAPD_SUPPORT 1
#define IEEE80211_ADDR_LEN 6
#define IEEE80211_KEYBUF_SIZE 16
#define IEEE80211_MICBUF_SIZE 16
#define NDIS_STATUS_SUCCESS 0
#define CIPHER_NONE 0
#define CIPHER_WEP64 1
#define CIPHER_WEP128 2
#define CIPHER_TKIP 3
#define CIPHER_AES 4
#define Ndis802_11TKIPEnable 10
#define Ndis802_11AESEnable 11
#define OFFSET_OF_PTK_TK 32
#define LEN_TK 16
#define PAIRWISEKEYTABLE 1
#define SHAREDKEYTABLE 0
'''+layouts+r'''
typedef struct {CIPHER_KEY PairwiseKey;unsigned char PTK[64];unsigned int func_tb_idx,wcid,WepStatus;} MAC_TABLE_ENTRY;
struct wifi_dev {unsigned int DefaultKeyId,GroupKeyWepStatus;};
typedef struct {struct wifi_dev wdev;} BSS_STRUCT;
typedef struct {struct {BSS_STRUCT MBSSID[3];} ApCfg;CIPHER_KEY SharedKey[3][4];} RTMP_ADAPTER;
static unsigned int writes;
static void io(RTMP_ADAPTER *ad,...){(void)ad;writes++;}
#define AsicAddPairwiseKeyEntry io
#define RTMPAddWcidAttributeEntry io
#define AsicAddSharedKeyEntry io
#define RTMPSetWcidSecurityInfo io
#define AsicRemovePairwiseKeyEntry io
#define AsicRemoveSharedKeyEntry io
#define GET_GroupKey_WCID(ad,wcid,index) do{(void)(ad);(wcid)=(index);}while(0)
#define NdisMoveMemory memcpy
#define NdisZeroMemory(dst,size) memset((dst),0,(size))
#define printk(...) ((void)0)
#define hex_dump(label,data,len) ((void)(data))
'''
main=r'''
int main(void){
 RTMP_ADAPTER ad={0};MAC_TABLE_ENTRY entry={0};struct ieee80211req_key key={0};struct ieee80211req_del_key del={0};
 entry.wcid=1;entry.func_tb_idx=2;entry.WepStatus=Ndis802_11AESEnable;
 key.ik_type=CIPHER_AES;key.ik_keylen=16;memset(key.ik_keydata,0x5a,16);
 assert(!wr_iot_hostapd_set_key_native(&ad,2,&entry,key));
 assert(writes==2&&entry.PairwiseKey.KeyLen==16&&entry.PairwiseKey.CipherAlg==CIPHER_AES);
 assert(!memcmp(entry.PairwiseKey.Key,key.ik_keydata,16));
 writes=0;ad.ApCfg.MBSSID[2].wdev.GroupKeyWepStatus=Ndis802_11AESEnable;key.ik_keyix=1;
 assert(!wr_iot_hostapd_set_key_native(&ad,2,NULL,key));
 assert(writes==2&&ad.ApCfg.MBSSID[2].wdev.DefaultKeyId==1);
 assert(!memcmp(ad.SharedKey[2][1].Key,key.ik_keydata,16));
 writes=0;assert(!wr_iot_hostapd_del_key_native(&ad,2,&entry,del));
 assert(writes==1&&!entry.PairwiseKey.KeyLen);
 writes=0;entry.wcid=0;assert(!wr_iot_hostapd_del_key_native(&ad,2,&entry,del)&&!writes);
 puts("Prepared wdev-layout correction: AES pair/group and pair delete host PASS; original helper layout rejected; full HOSTAPD/target unverified");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-hostapd-key-native-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(prefix+helpers+main)
 # Native DEL tests an embedded address array against NULL. Preserve that
 # existing branch for this factoring test; protocol correction is separate.
 command=['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-address','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(exe)]
 control=subprocess.run(command,capture_output=True,text=True)
 assert control.returncode and 'DefaultKeyId' in control.stderr and 'GroupKeyWepStatus' in control.stderr
 patched=runpy.run_path(str(here/'hostapd-key-layout-composition.py'))['compose'](helpers)
 # Verify real source puts the security fields in wifi_dev, not BSS_STRUCT.
 header=(a.source/'include/rtmp.h').read_text()
 wifi=header[header.index('struct wifi_dev{'):header.index('struct wifi_dev{')+4000]
 assert 'UCHAR DefaultKeyId;' in wifi and 'NDIS_802_11_WEP_STATUS GroupKeyWepStatus;' in wifi
 bss=structure(header,'typedef struct _BSS_STRUCT {','} BSS_STRUCT;')
 assert 'struct wifi_dev wdev;' in bss and 'DefaultKeyId;' not in bss and 'GroupKeyWepStatus;' not in bss
 src.write_text(prefix+patched+main)
 subprocess.run(command,check=True)
 subprocess.run([str(exe)],check=True)
