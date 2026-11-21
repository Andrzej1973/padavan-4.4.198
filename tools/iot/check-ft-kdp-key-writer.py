#!/usr/bin/env python3
"""Execute prepared native key writer; password hash is a deterministic actor."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
saved=sys.argv[:];sys.argv=[str(here/'check-ft-kdp-crypto.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):fixture=runpy.run_path(sys.argv[0])
finally:sys.argv=saved
source=(a.source/'ap/ap_ftkd.c').read_text(encoding='latin1');caller=(a.source/'ap/ap_cfg.c').read_text(encoding='latin1');header=(a.source/'include/ft.h').read_text()
changed,caller,header=runpy.run_path(str(here/'ft-kdp-key-writer-composition.py'))['compose'](source,caller,header)
start=changed.index('static BOOLEAN wr_native_kdp_key_set(');end=changed.index('\n}',changed.index('BOOLEAN wr_ft_kdp_key_set_checked(',start))+2
code=changed[start:end]
assert 'if(!wr_ft_kdp_key_set_checked(pAd,pBuffer,wrq->u.data.length))Status=-EAGAIN;' in caller
prefix=fixture['prefix'].replace('CryptKey[16]','CryptKey[100]')
actor=r'''
typedef int INT32;typedef char RTMP_STRING;typedef UCHAR *PUCHAR;
#define FT_KDP_RALINK_PASSPHRASE "Ralink"
#define FT_KDP_KEY_DEFAULT "12345678"
static int hashes,default_used,hash_failure;
static int RtmpPasswordHash(RTMP_STRING *key,PUCHAR salt,size_t length,UCHAR *out){
 assert(!held&&observed->wr_ft_cache_lifetime.owner.transactions==1);
 assert(length==6&&!memcmp(salt,"Ralink",6));hashes++;
 default_used=!strcmp(key,"12345678");memset(out,0x42,40);
 assert(wr_ft_cache_close(&observed->wr_ft_cache_lifetime));
 assert(!wr_ft_cache_destroy_begin(&observed->wr_ft_cache_lifetime));
 return !hash_failure;
}
'''
case_start=caller.rfind('case RT_FT_KEY_SET:',0,caller.index('/* Note: the key must be ended by 0x00 */'))
case_end=caller.index('case RT_FT_NEIGHBOR_REPORT:',case_start)
case=caller[case_start:case_end]
assert 'wr_ft_kdp_key_set_checked(' in case
actor+=r'''
#define RT_FT_KEY_SET 4
BOOLEAN wr_ft_kdp_key_set_checked(RTMP_ADAPTER *,UCHAR *,INT32);
struct key_request {struct {struct {unsigned int length;}data;}u;};
'''
actor+='static int key_ioctl(RTMP_ADAPTER *pAd,UCHAR *input,unsigned int length){\n'
actor+='struct key_request request={.u.data={.length=length}},*wrq=&request;\n'
actor+='UCHAR *pBuffer;int Status=0,cmd=RT_FT_KEY_SET;\n'
actor+='FT_MEM_ALLOC(pAd,&pBuffer,length+1);memcpy(pBuffer,input,length);\n'
actor+='switch(cmd){'+case+'default:assert(0); }\n'
wipe_start=caller.index('if((cmd & 0x7FFF)==RT_FT_KEY_SET){')
wipe_end=caller.index('FT_MEM_FREE(pAd, pBuffer);',wipe_start)
wipe=caller[wipe_start:wipe_end]
assert caller.count(wipe)==2
actor+=wipe
actor+='for(unsigned int i=0;i<length+1;i++)assert(pBuffer[i]==0);\n'
actor+='FT_MEM_FREE(pAd,pBuffer);return Status; }\n'
fault_start=caller.index('Status = -EFAULT;',caller.index('case RT_SET_FT_STATION_NOTIFY:'))
fault_end=caller.index('break;',fault_start)
fault=caller[fault_start:fault_end]
assert wipe in fault
actor+='static void key_copy_fault(RTMP_ADAPTER *pAd,unsigned int length){\n'
actor+='struct key_request request={.u.data={.length=length}},*wrq=&request;\n'
actor+='int Status=0,cmd=RT_FT_KEY_SET;UCHAR *pBuffer;\n'
actor+='FT_MEM_ALLOC(pAd,&pBuffer,length+1);memset(pBuffer,0xa5,length+1);\n'
# Replace only free actor to observe bytes immediately before actual release.
observed_fault=fault.replace('FT_MEM_FREE(pAd, pBuffer);',
 'for(unsigned int i=0;i<length+1;i++)assert(!pBuffer[i]);\n FT_MEM_FREE(pAd,pBuffer);')
actor+=observed_fault+'assert(Status==-EFAULT); }\n'
main=r'''
int main(void){
 for(int scenario=0;scenario<5;scenario++){
  RTMP_ADAPTER ad={0};BLOCK block={{0}};UCHAR key[]="password123";unsigned long serial;
  observed=&ad;ad.ApCfg.FtTab.pFT_KDP_Ctrl_BK=&block;ad.ApCfg.FtTab.FlgIsFtKdpInit=1;
  ad.wr_ft_cache_lifetime_initialized=1;wr_ft_cache_lifetime_init(&ad.wr_ft_cache_lifetime);
  serial=wr_ft_cache_start(&ad.wr_ft_cache_lifetime);assert(wr_ft_cache_publish(&ad.wr_ft_cache_lifetime,serial,1));
  hash_failure=scenario==4;int before=hashes;if(scenario==1)assert(wr_ft_cache_close(&ad.wr_ft_cache_lifetime));
  if(scenario==2)ad.ApCfg.FtTab.pFT_KDP_Ctrl_BK=NULL;
  int status=key_ioctl(&ad,key,scenario==3?7:11);
  int ok=status==0;
  if(!ok)assert(status==-EAGAIN);
#ifdef FT_KDP_EMPTY
  assert(!ok&&hashes==before);
#else
  if(scenario==0||scenario==3){
   assert(ok&&hashes==before+1&&default_used==(scenario==3));
   for(unsigned i=0;i<100;i++)assert(block.CryptKey[i]==(i<40?0x42:0));
  }else if(scenario==4){assert(!ok&&hashes==before+1);for(unsigned i=0;i<100;i++)assert(!block.CryptKey[i]);}
  else assert(!ok&&hashes==before);
#endif
  assert(!held&&!ad.wr_ft_cache_lifetime.owner.transactions);
  assert(allocations==frees);
  for(unsigned int length=0;length<=65;length++)key_copy_fault(&ad,length);
  assert(allocations==frees);
 }
 puts("PASS | KDP checked key writer | native hash selection/publication, closed/missing refusal, lease survives close during hash; hash substituted");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='kdp-key-writer-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+actor+code+main)
 for i,flags in enumerate(([],['-DFT_KDP_EMPTY'])):
  exe=Path(td)/str(i)
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(c),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
