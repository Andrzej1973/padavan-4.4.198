#!/usr/bin/env python3
"""Extract disconnect-all caller and assert direct reset refusal coverage."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
ap=(a.candidate/'ap/ap.c').read_text()
cfg=(a.candidate/'ap/ap_cfg.c').read_text()
info=(a.candidate/'common/cmm_info.c').read_text()
header=(a.candidate/'include/rtmp.h').read_text()
assert 'BOOLEAN MacTableReset(' in header and 'BOOLEAN MacTableResetWdev(' in header
assert 'VOID MacTableReset(' not in header and 'VOID MacTableResetWdev(' not in header
stop_checked='BOOLEAN APStop(' in ap
stop_type='BOOLEAN' if stop_checked else 'VOID'
stop_return='return FALSE;' if stop_checked else 'return;'
for signature,guard,tail in [
 (stop_type+' APStop(', 'if (!MacTableReset(pAd, 1)) '+stop_return, 'RTMP_SET_FLAG(pAd, fRTMP_ADAPTER_HALT_IN_PROGRESS)'),
 (stop_type+' APStopBssOnly(', 'if (!MacTableResetWdev(pAd, wdev_bss)) '+stop_return, 'AsicSetPreTbtt(pAd, FALSE)'),
]:
 start=ap.index(signature);end=ap.index('\n}',start)+2;body=ap[start:end]
 assert body.count(guard)==1 and body.index(guard)<body.index(tail)
assert info.count('if (!MacTableResetWdev(pAd, pAd->wdev_list[i])) return FALSE;')==2
start=cfg.index('INT Set_DisConnectAllSta_Proc(\n');end=cfg.index('\n}',start)+2
body=cfg[start:end]
assert 'if (!MacTableReset(pAd, 1)) return FALSE;' in body
assert 'if (!MacTableDeleteEntry(pAd, pEntry->wcid, pEntry->Addr)) return FALSE;' in body
prefix=r'''
#include <assert.h>
#include <stdlib.h>
#define IN
#define TRUE 1
#define FALSE 0
#define MAX_LEN_OF_MAC_TABLE 4
#define RT_DEBUG_WARN 0
#define RT_DEBUG_ERROR 0
#define REASON_DEAUTH_STA_LEAVING 1
#define DBGPRINT(l,a) do{(void)(l);}while(0)
typedef int INT;typedef char CHAR;typedef char RTMP_STRING;
typedef struct {int kind,wcid;unsigned char Addr[6];} MAC_TABLE_ENTRY;
typedef struct {int ioctl_if;} COOKIE,*POS_COOKIE;
typedef struct {void *OS_Cookie;struct {MAC_TABLE_ENTRY Content[4];} MacTab;} RTMP_ADAPTER,*PRTMP_ADAPTER;
static int reset_result,reset_calls;
static int MacTableReset(RTMP_ADAPTER *a,int first){(void)a;(void)first;reset_calls++;return reset_result;}
#ifdef DOT11W_PMF_SUPPORT
static int delete_result,delete_calls,kicked;
#define simple_strtol strtol
#define IS_ENTRY_CLIENT(e) ((e)->kind==1)
static void APMlmeKickOutAllSta(RTMP_ADAPTER *a,int idx,int reason){(void)a;(void)idx;(void)reason;kicked++;}
static int MacTableDeleteEntry(RTMP_ADAPTER *a,int wcid,unsigned char *addr){(void)a;(void)wcid;(void)addr;delete_calls++;return delete_result;}
#endif
'''
suffix=r'''
int main(void){COOKIE cookie={0};RTMP_ADAPTER a={0};a.OS_Cookie=&cookie;
reset_result=0;assert(!Set_DisConnectAllSta_Proc(&a,"0")&&reset_calls==1);
reset_result=1;assert(Set_DisConnectAllSta_Proc(&a,"0")&&reset_calls==2);
#ifdef DOT11W_PMF_SUPPORT
a.MacTab.Content[1].kind=a.MacTab.Content[2].kind=1;delete_result=0;
assert(!Set_DisConnectAllSta_Proc(&a,"2")&&delete_calls==1&&kicked==1&&reset_calls==2);
delete_result=1;delete_calls=0;
assert(Set_DisConnectAllSta_Proc(&a,"2")&&delete_calls==2&&kicked==2&&reset_calls==2);
#else
reset_result=0;assert(!Set_DisConnectAllSta_Proc(&a,"2")&&reset_calls==3);
#endif
return 0;}
'''
if 'DOT11W_PMF_SUPPORT' not in prefix:p.error('fixture feature gate missing')
# Without PMF, upstream signature retains an unused arg. Use it explicitly in
# the fixture only; the original driver does not enable host -Wextra globally.
body=body.replace('{\n#ifdef DOT11W_PMF_SUPPORT','{\n (void)arg;\n#ifdef DOT11W_PMF_SUPPORT',1)
a.output.write_text(prefix+body+suffix,encoding='utf-8')
print('Extracted disconnect-all result; five direct reset guards asserted, APStop parents unproved')
