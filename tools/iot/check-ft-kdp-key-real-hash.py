#!/usr/bin/env python3
"""Checked writer + pinned password derivation; system HMAC, host actors."""
import argparse,contextlib,hashlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
saved=sys.argv[:]
try:
 with contextlib.redirect_stdout(io.StringIO()):
  sys.argv=[str(here/'check-ft-kdp-key-writer.py'),str(a.source)]
  writer=runpy.run_path(sys.argv[0])
  sys.argv=[str(here/'check-ft-kdp-password-hash.py'),str(a.source)]
  derivation=runpy.run_path(sys.argv[0])
finally:sys.argv=saved
# Reuse actual generated writer body and native F/RtmpPasswordHash. The actor's
# ioctl helpers are excluded; this fixture executes writer publication itself.
prefix=writer['prefix']
hmac=derivation['body'].split(derivation['native'],1)[0]
# Prefix declares UCHAR, RTMP_ADAPTER and native lock/memory actors already.
hmac=hmac[hmac.index('#define SHA1_DIGEST_SIZE'):]
types='typedef int INT32;typedef int INT;typedef char RTMP_STRING;typedef UCHAR *PUCHAR;\n'
constants='#define FT_KDP_RALINK_PASSPHRASE "Ralink"\n#define FT_KDP_KEY_DEFAULT "12345678"\n'
main=r'''
int main(int argc,char **argv){
 RTMP_ADAPTER ad={0};BLOCK block;unsigned long serial;
 assert(argc==2);memset(&block,0xa5,sizeof(block));observed=&ad;
 ad.ApCfg.FtTab.pFT_KDP_Ctrl_BK=&block;ad.ApCfg.FtTab.FlgIsFtKdpInit=1;
 ad.wr_ft_cache_lifetime_initialized=1;wr_ft_cache_lifetime_init(&ad.wr_ft_cache_lifetime);
 serial=wr_ft_cache_start(&ad.wr_ft_cache_lifetime);
 assert(wr_ft_cache_publish(&ad.wr_ft_cache_lifetime,serial,1));
 UCHAR malformed[12]="password123";
 malformed[4]=0;
 assert(!wr_ft_kdp_key_set_checked(&ad,malformed,11));
 malformed[4]='w';malformed[11]='x';
 assert(!wr_ft_kdp_key_set_checked(&ad,malformed,11));
 for(unsigned i=0;i<100;i++)assert(block.CryptKey[i]==0xa5);
 assert(!ad.wr_ft_cache_lifetime.owner.transactions);
 int ok=wr_ft_kdp_key_set_checked(&ad,(UCHAR *)argv[1],strlen(argv[1]));
 assert(!held&&!ad.wr_ft_cache_lifetime.owner.transactions);
 if(!ok){for(unsigned i=0;i<100;i++)assert(block.CryptKey[i]==0xa5);puts("REFUSED");return 0;}
 for(unsigned i=40;i<100;i++)assert(block.CryptKey[i]==0xa5);
 for(unsigned i=0;i<40;i++)printf("%02x",block.CryptKey[i]);puts("");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-real-writer-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check'
 c.write_text(prefix+types+constants+hmac+derivation['native']+writer['code']+main)
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-Wl,-l:libcrypto.so.3','-o',str(exe)],check=True)
 for key in ('12345678','password123','x'*63,'x'*64,'short'):
  result=subprocess.check_output([str(exe),key],text=True).strip()
  desired='REFUSED' if len(key)==64 else hashlib.pbkdf2_hmac('sha1',(key if len(key)>=8 else '12345678').encode(),b'Ralink',4096,40).hex()
  assert result==desired
print('PASS | checked KDP writer + native F/RtmpPasswordHash | 40-byte publication matches PBKDF2, short default, 63-byte success, 64-byte refusal preserves old key; system HMAC, host only')
