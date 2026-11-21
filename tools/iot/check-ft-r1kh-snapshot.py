#!/usr/bin/env python3
"""Execute the generated snapshot API with the pinned native cache entry type."""
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
source=(a.source/'common/ft.c').read_text()
header=(a.source/'include/ft.h').read_text()
changed,decl=api['compose'](source,header)
assert changed.count(api['FUNCTION'])==1
assert changed.count('wr_ft_r1kh_snapshot(pAd, pEntry->FT_PMK_R1_NAME, pR1hkEntry)')==2
assert 'wr_ft_r1kh_snapshot(pAd, OriPMKR1Name, pR1khEntry)' in changed
assert 'wr_ft_r1kh_delete' in api['FUNCTION'] and 'wr_ft_r1kh_delete' in api['PROTOTYPE']
assert changed.count('wr_ft_r1kh_snapshot(pAd, pEntry->FT_PMK_R1_NAME, &r1khSnapshot) ? &r1khSnapshot : NULL;')==2
assert changed.count('FT_R1khEntryTabLookup(pAd,')==0
assert changed.count('FT_R1khEntryDelete(pAd,')==0
assert 'return wr_ft_r1kh_store_fields(pAd,pPmkR0Name,pPmkR1Name,pPmkR1Key,' in changed
assert 'pEntry->Addr) < 0) return MLME_FAIL_NO_RESOURCE;' in changed
related={name:(a.source/name).read_text(encoding='latin1')
 for name in ('common/cmm_wpa.c','ap/ap_ftkd.c')}
related=api['compose_related'](related)
for name,text in related.items():
    assert 'FT_R1khEntryTabLookup(' not in text
    assert 'FT_R1khEntryDelete(' not in text
    assert 'wr_ft_r1kh_snapshot(' in text
assert 'FT_R1khEntryInsert(pAd,' in related['common/cmm_wpa.c']
assert 'FT_R1khEntryInsert(pAd,' in related['ap/ap_ftkd.c']
response=related['ap/ap_ftkd.c']
response=response[response.index('VOID TYPE_FUNC FT_KDP_KeyResponseToUs('):]
response=response[:response.index('\n}')+2]
assert response.index('InfoLen < 0') < response.index('IAPP_DAEMON_CMD_PARSE(pInfo,')
assert 'pEvtKeyRsp = &wr_owned_response;' in response
assert 'pEvtKeyRsp = (FT_KDP_EVT_KEY_ELM *)' not in response
assert response.index('KeyInfo.R0KHIDLen > sizeof') < response.index('wr_ft_r1kh_snapshot(')
store_start=response.index('if (FT_R1khEntryInsert(pAd,')
refusal=response.index('< 0) return;',store_start)
assert refusal < response.index('pEntry->FT_R1kh_CacheMiss_Times = 0;')
assert refusal < response.index('RTMP_OS_COMPLETE(&pEntry->ack_r1kh);')

assert decl.replace(api['PROTOTYPE']+'\n\n','',1)==header
try:
    api['compose'](changed,decl)
except ValueError:
    pass
else:
    raise AssertionError('duplicate snapshot preparation accepted')
# Mutations must fail closed instead of producing a partially converted TU.
pristine_related={name:(a.source/name).read_text(encoding='latin1')
 for name in ('common/cmm_wpa.c','ap/ap_ftkd.c')}
for filename,anchor in (
 ('ap/ap_ftkd.c','FT_R1khEntryInsert(pAd,'),
 ('ap/ap_ftkd.c','pR1hkEntry = FT_R1khEntryTabLookup(pAd, pEvtKeyRsp->PMKR1Name);'),
 ('common/cmm_wpa.c','PFT_R1HK_ENTRY pR1khEntry;')):
    assert pristine_related[filename].count(anchor)==1
    for replacement in ('/* missing anchor */',anchor+anchor):
        mutated=dict(pristine_related)
        mutated[filename]=mutated[filename].replace(anchor,replacement,1)
        try: api['compose_related'](mutated)
        except ValueError: pass
        else: raise AssertionError('source drift accepted: '+filename+' '+anchor)
try: api['compose_related'](related)
except ValueError: pass
else: raise AssertionError('duplicate related-source composition accepted')
print('PASS | FT composition drift | missing/duplicate caller anchors and repeated composition refused')
# Execute the actual composed AUTH lookup and its native cache-miss predicate.
auth_start=changed.rindex('UINT16\tFT_AuthReqRsnValidation(')
auth=changed[auth_start:changed.index('\n}',auth_start)+2]
lookup_start=auth.index('pR1hkEntry = wr_ft_r1kh_snapshot', auth.index('R1KH_QUERY:'))
lookup=auth[lookup_start:auth.index(';',lookup_start)+1]
predicate_start=auth.index('if ((pR1hkEntry == NULL)',lookup_start)
predicate=auth[predicate_start:auth.index('{',predicate_start)]
retry_probe="""
#define LEN_PMK_NAME 16
static int auth_cache_miss(RTMP_ADAPTER *pAd, unsigned char *name){
 struct {unsigned char FT_PMK_R1_NAME[16];} entry, *pEntry=&entry;
 FT_R1HK_ENTRY r1khSnapshot; PFT_R1HK_ENTRY pR1hkEntry=NULL;
 memcpy(entry.FT_PMK_R1_NAME,name,16);
"""+lookup+"\n"+predicate+" return 1;\n return 0;\n}\n"
types=(a.source/'include/ft_cmm.h').read_text()
start=types.index('typedef struct __FT_R1KH_ENTRY')
end=types.index('} FT_R1HK_ENTRY, *PFT_R1HK_ENTRY;',start)+len('} FT_R1HK_ENTRY, *PFT_R1HK_ENTRY;')
prefix=r'''
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
typedef unsigned char UINT8,UCHAR;
typedef unsigned int UINT32; typedef int INT; typedef unsigned char *PUINT8;
typedef int BOOLEAN;
#define TRUE 1
#define FALSE 0
#define FT_ROKH_ID_LEN 48
#define FT_KDP_WPA_NAME_MAX_SIZE 16
#define FT_R1KH_HASH_INDEX(name) 0
#define MAC_ADDR_LEN 6
#define LEN_PMK 32
'''+types[start:end]+(a.source/'include/link_list.h').read_text()+r'''
typedef struct {struct {struct {int FT_R1khEntryTabLock,FT_R1khEntryTabReady;
 unsigned int FT_R1khEntryTabSize;
 LIST_HEADER FT_R1khEntryTab[1];} FtTab;} ApCfg;} RTMP_ADAPTER;
static FT_R1HK_ENTRY *retire_on_unlock;
static int held;
static int fail_alloc,allocations,frees;
static RTMP_ADAPTER *observed_adapter;
#define NDIS_STATUS_SUCCESS 0
#define FT_R1KH_ENTRY_TABLE_SIZE 2
static int os_alloc_mem(void *ad,UCHAR **out,size_t n){
 (void)ad;assert(!held);if(fail_alloc)return 1;
 *out=calloc(1,n);if(!*out)return 1;
 allocations++;return 0;
}
static void os_free_mem(void *ad,void *p){(void)ad;assert(!held);free(p);frees++;}
static void lock_cache(int *lock){assert(!*lock&&!held);*lock=held=1;}
static void unlock_cache(int *lock){assert(*lock&&held);*lock=held=0;
 if(retire_on_unlock){free(retire_on_unlock);retire_on_unlock=NULL;}}
static int cache_overlap(const void *p,size_t n){
 uintptr_t address=(uintptr_t)p;
 FT_R1HK_ENTRY *node=observed_adapter ?
  (FT_R1HK_ENTRY *)observed_adapter->ApCfg.FtTab.FT_R1khEntryTab[0].pHead : NULL;
 while(node){uintptr_t base=(uintptr_t)node;
  if(n && address<base+sizeof(*node) && base<address+n)return 1;
  node=node->pNext;
 }
 return 0;
}
static void copy_locked(void *out,const void *in,size_t n){
 assert(held||(!cache_overlap(in,n)&&!cache_overlap(out,n)));
 memcpy(out,in,n);
}
#define RTMP_SEM_LOCK(p) lock_cache(p)
#define RTMP_SEM_UNLOCK(p) unlock_cache(p)
#define RTMPEqualMemory(a,b,n) (!memcmp(a,b,n))
#define NdisZeroMemory(p,n) memset(p,0,n)
#define NdisMoveMemory(p,q,n) copy_locked(p,q,n)
'''
main=r'''
int main(void){
 RTMP_ADAPTER ad={0};FT_R1HK_ENTRY out;observed_adapter=&ad;
 unsigned char name[16]={7},miss[16]={8};
 FT_R1HK_ENTRY *first=calloc(1,sizeof(*first)),*second=calloc(1,sizeof(*second));
 assert(first&&second);first->pNext=second;first->PmkR1Name[0]=1;
 memcpy(second->PmkR1Name,name,16);second->PmkR1Key[0]=99;
 second->R0khIdLen=48;second->R0khId[47]=42;second->KeyLifeTime=17;
 ad.ApCfg.FtTab.FT_R1khEntryTab[0].pHead=(RT_LIST_ENTRY *)first;
 memset(&out,0x55,sizeof(out));
 assert(!wr_ft_r1kh_snapshot(&ad,name,&out));
 assert(!out.pNext&&!out.PmkR1Key[0]&&!held);
 ad.ApCfg.FtTab.FT_R1khEntryTabReady=1;
 assert(!wr_ft_r1kh_snapshot(&ad,miss,&out)&&!out.PmkR1Key[0]);
 second->R0khIdLen=49;
 assert(!wr_ft_r1kh_snapshot(&ad,name,&out)&&!out.PmkR1Key[0]);
 second->R0khIdLen=48;
 retire_on_unlock=second;
 assert(wr_ft_r1kh_snapshot(&ad,name,&out));
 /* The matched native node was freed at unlock; no pointer may escape. */
 first->pNext=NULL;
 assert(!out.pNext&&out.PmkR1Key[0]==99&&out.KeyLifeTime==17&&out.R0khId[47]==42&&!held);
 assert(!wr_ft_r1kh_snapshot(NULL,name,&out)&&!out.PmkR1Key[0]);
 assert(!wr_ft_r1kh_snapshot(&ad,NULL,&out)&&!out.PmkR1Key[0]);
 assert(!wr_ft_r1kh_snapshot(&ad,name,NULL)&&!held);
 free(first);
 ad.ApCfg.FtTab.FT_R1khEntryTab[0]=(LIST_HEADER){0};
 FT_R1HK_ENTRY value={0};value.PmkR1Name[0]=7;value.PmkR1Key[0]=10;
 assert(wr_ft_r1kh_store(&ad,&value));
 assert(ad.ApCfg.FtTab.FT_R1khEntryTabSize==1);
 assert(wr_ft_r1kh_snapshot(&ad,name,&out)&&out.PmkR1Key[0]==10);
 assert(!auth_cache_miss(&ad,name));
 assert(auth_cache_miss(&ad,miss));
 unsigned char key[32]={21},cipher[4]={1,2,3,4},akm[4]={5,6,7,8},r0[2]={9,10},mac[6]={2,3,4,5,6,7};
 assert(wr_ft_r1kh_store_fields(&ad,NULL,name,key,cipher,akm,50,20,r0,2,mac)==0);
 assert(wr_ft_r1kh_snapshot(&ad,name,&out)&&out.PmkR1Key[0]==21&&out.PairwisChipher[3]==4&&out.AkmSuite[0]==5&&out.R0khIdLen==2&&out.StaMac[5]==7&&out.KeyLifeTime==50);
 assert(wr_ft_r1kh_store_fields(&ad,NULL,NULL,key,cipher,akm,50,20,r0,2,mac)==-1);
 FT_R1HK_ENTRY response_value={0};memcpy(response_value.PmkR1Name,name,16);
 response_value.PmkR1Key[0]=21;response_value.KeyLifeTime=99;
 assert(wr_ft_r1kh_response_store(&ad,&response_value)==0);
 assert(wr_ft_r1kh_snapshot(&ad,name,&out)&&out.PmkR1Key[0]==21&&out.KeyLifeTime==50);
 response_value.PmkR1Key[0]=22;
 assert(wr_ft_r1kh_response_store(&ad,&response_value)==1);
 assert(ad.ApCfg.FtTab.FT_R1khEntryTabSize==1);
 assert(wr_ft_r1kh_snapshot(&ad,name,&out)&&out.PmkR1Key[0]==22);
 fail_alloc=1;response_value.PmkR1Key[0]=23;
 assert(wr_ft_r1kh_response_store(&ad,&response_value)==-1);
 assert(wr_ft_r1kh_snapshot(&ad,name,&out)&&out.PmkR1Key[0]==22);
 fail_alloc=0;
 fail_alloc=1;value.PmkR1Key[0]=11;
 assert(!wr_ft_r1kh_store(&ad,&value));
 assert(wr_ft_r1kh_snapshot(&ad,name,&out)&&out.PmkR1Key[0]==22);
 fail_alloc=0;assert(wr_ft_r1kh_store(&ad,&value));
 assert(wr_ft_r1kh_snapshot(&ad,name,&out)&&out.PmkR1Key[0]==11);
 assert(ad.ApCfg.FtTab.FT_R1khEntryTabSize==1);
 value.PmkR1Name[0]=8;assert(wr_ft_r1kh_store(&ad,&value));
 value.PmkR1Name[0]=9;assert(!wr_ft_r1kh_store(&ad,&value));
 assert(ad.ApCfg.FtTab.FT_R1khEntryTabSize==2);
 value.PmkR1Name[0]=7;value.PmkR1Key[0]=12;
 assert(wr_ft_r1kh_store(&ad,&value)); /* replacement allowed at capacity */
 assert(wr_ft_r1kh_snapshot(&ad,name,&out)&&out.PmkR1Key[0]==12);
 LIST_HEADER *bucket=&ad.ApCfg.FtTab.FT_R1khEntryTab[0];
 assert(bucket->size==2&&bucket->pHead&&bucket->pTail&&!bucket->pTail->pNext);
 assert(wr_ft_r1kh_delete(&ad,name));
 assert(ad.ApCfg.FtTab.FT_R1khEntryTabSize==1&&bucket->size==1);
 assert(!wr_ft_r1kh_snapshot(&ad,name,&out)&&!out.PmkR1Key[0]);
 assert(!wr_ft_r1kh_delete(&ad,name));
 ad.ApCfg.FtTab.FT_R1khEntryTabReady=0;
 assert(!wr_ft_r1kh_store(&ad,&value));
 value.R0khIdLen=49;assert(!wr_ft_r1kh_store(&ad,&value));
 assert(!wr_ft_r1kh_store(NULL,&value));assert(!wr_ft_r1kh_store(&ad,NULL));
 while(bucket->pHead)os_free_mem(&ad,removeHeadList(bucket));
 assert(allocations==frees&&!held);
 puts("PASS | FT AUTH cache miss | actual composed lookup and native predicate preserve miss request admission and cached hit");
 puts("PASS | FT R1KH snapshot | locked value copy survives immediate node retirement; miss, closed cache, invalid length and null refusal");
 puts("PASS | FT response cache transaction | atomic unchanged/update results, capacity invariant and allocation-failure preservation");
 puts("PASS | FT R1KH atomic store/delete | fields create owned entry; allocation failure preserves prior value; replace/full refusal, key delete and allocation balance");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-r1kh-snapshot-') as td:
    c=Path(td)/'check.c'
    exe=Path(td)/'check'
    c.write_text(prefix+api['FUNCTION']+retry_probe+main)
    subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
    # Negative control: deliberately copy a still-linked cache field unlocked.
    negative_main=r"""
int main(void){
 RTMP_ADAPTER ad={0}; FT_R1HK_ENTRY entry={0}; unsigned char out[4];
 observed_adapter=&ad;
 ad.ApCfg.FtTab.FT_R1khEntryTab[0].pHead=(RT_LIST_ENTRY *)&entry;
 copy_locked(out,entry.AkmSuite,sizeof(out));
 return 0;
}
"""
    c.write_text(prefix+api['FUNCTION']+negative_main)
    subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],check=True)
    rejected=subprocess.run([str(exe)],capture_output=True,text=True)
    assert rejected.returncode!=0 and 'cache_overlap' in rejected.stderr
    print('PASS | FT cache lock negative control | unlocked four-byte cache read rejected')

print('PASS | FT R1KH snapshot composition | KDP query plus AUTH-CONFIRM and ASSOC readers converted; FT readers, AUTH and cmm writers, and IAPP response cache access compose to owned snapshots/atomic replacement; response identity still unverified')
