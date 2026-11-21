#!/usr/bin/env python3
"""Execute pinned password derivation; system libcrypto supplies HMAC-SHA1."""
import argparse,hashlib,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
source=(a.source/'common/cmm_wpa.c').read_text(encoding='latin1')
def function(signature):
 start=source.index(signature);end=source.index('\n}',start)+2
 return source[start:end]
native=function('static void F(')+'\n'+function('int RtmpPasswordHash(')
body=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stddef.h>
typedef char RTMP_STRING;typedef unsigned char *PUCHAR;typedef int INT;
#define SHA1_DIGEST_SIZE 20
typedef struct evp_md_st EVP_MD;
extern const EVP_MD *EVP_sha1(void);
extern unsigned char *HMAC(const EVP_MD *,const void *,int,const unsigned char *,size_t,unsigned char *,unsigned int *);
static void RT_HMAC_SHA1(unsigned char *key,int keylen,unsigned char *data,int len,unsigned char *out,int size){
 unsigned char digest[20];unsigned int n=0;
 assert(size==20&&HMAC(EVP_sha1(),key,keylen,data,(size_t)len,digest,&n)&&n==20);
 memcpy(out,digest,20);
}
'''+native+r'''
int main(int argc,char **argv){
 unsigned char out[40];assert(argc==2);memset(out,0xa5,sizeof(out));
 int ok=RtmpPasswordHash(argv[1],(unsigned char *)"Ralink",6,out);
 if(!ok){for(unsigned i=0;i<40;i++)assert(out[i]==0xa5);puts("REFUSED");return 0;}
 for(unsigned i=0;i<40;i++)printf("%02x",out[i]);puts("");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-password-hash-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check';c.write_text(body)
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-Wl,-l:libcrypto.so.3','-o',str(exe)],check=True)
 for key in ('12345678','password123','x'*63,'x'*64):
  result=subprocess.check_output([str(exe),key],text=True).strip()
  assert result==('REFUSED' if len(key)>63 else hashlib.pbkdf2_hmac('sha1',key.encode(),b'Ralink',4096,40).hex())
print('PASS | native RtmpPasswordHash/F | default, supplied, 63-byte derivation matches independent PBKDF2; 64-byte refusal preserves output; system HMAC primitive, host only')
