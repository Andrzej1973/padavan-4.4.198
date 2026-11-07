#!/usr/bin/env python3
"""Execute actual vendor SHA1/HMAC/PBKDF against independent hashlib vectors and key matcher."""
import argparse,hashlib,json,re,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
files={n:(a.driver/n).read_bytes() for n in ['common/crypt_sha2.c','common/crypt_hmac.c','common/cmm_wpa.c','include/crypt_sha2.h']}
def clean(b):return re.sub(r'/\*.*?\*/|//[^\n]*','',b.decode('latin-1'),flags=re.S)
def function(text,name):
 m=re.search(r'(?:static\s+)?(?:VOID|void|int)\s+'+name+r'\s*\([^;]*?\)\s*\{',text);assert m,name
 level=1;pos=m.end()
 while level:
  if text[pos]=='{':level+=1
  if text[pos]=='}':level-=1
  pos+=1
 return text[m.start():pos]
sha=clean(files['common/crypt_sha2.c']);hmac=clean(files['common/crypt_hmac.c']);wpa=clean(files['common/cmm_wpa.c']);header=clean(files['include/crypt_sha2.h'])
header=header[header.index('#define SHA1_BLOCK_SIZE'):header.index('#endif /* SHA1_SUPPORT */')] if '#endif /* SHA1_SUPPORT */' in header else header[header.index('#define SHA1_BLOCK_SIZE'):header.index('#endif',header.index('#define SHA1_BLOCK_SIZE'))]
constants=sha[sha.index('static const UINT32 SHA1_K'):sha.index('#endif',sha.index('static const UINT32 SHA1_K'))]
prefix=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef void VOID;typedef unsigned int UINT;typedef uint32_t UINT32;typedef uint64_t UINT64;typedef unsigned char UINT8,UCHAR,*PUCHAR;typedef int INT;typedef char RTMP_STRING;
#define IN
#define OUT
#define NdisMoveMemory memcpy
#define NdisZeroMemory(p,n) memset(p,0,n)
#define NdisFillMemory(p,n,v) memset(p,v,n)
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
#define cpu2be32(x) __builtin_bswap32(x)
#define cpu2be64(x) __builtin_bswap64(x)
#else
#define cpu2be32(x) (x)
#define cpu2be64(x) (x)
#endif
#define ROTL32(x,n) (((x)<<(n))|((x)>>(32-(n))))
#define Ch(x,y,z) (((x)&(y))^((~(x))&(z)))
#define Maj(x,y,z) (((x)&(y))^((x)&(z))^((y)&(z)))
#define Parity(x,y,z) ((x)^(y)^(z))
'''
functions='\n'.join(function(sha,n) for n in ['RT_SHA1_Init','RT_SHA1_Hash','RT_SHA1_Append','RT_SHA1_End','RT_SHA1'])+'\n'+function(hmac,'RT_HMAC_SHA1')+'\n'+function(wpa,'F')+'\n'+function(wpa,'RtmpPasswordHash')
fixture='\n#define main old_matcher_fixture\n#include "check-precreated-loaded-config.c"\n#undef main\n#include "precreated-key-match.h"\nint main(void){RTMP_ADAPTER ad={.mt7603=1,.ApCfg.BssidNum=3};struct device dev={1};BSS_STRUCT *b=&ad.ApCfg.MBSSID[2];b->wdev.if_dev=&dev;b->wdev.AuthMode=7;b->wdev.WepStatus=b->wdev.GroupKeyWepStatus=3;\n'
vectors=[(b'password',b'IEEE'),(b'ThisIsAPassword',b'ThisIsASSID'),(b'x'*63,b's'*32),(b'12345678',b'IoT')]
for password,ssid in vectors:
 pmk=hashlib.pbkdf2_hmac('sha1',password,ssid,4096,32)
 fixture+='{unsigned char expected[32]={'+','.join(map(str,pmk))+'};char pass[]='+json.dumps(password.decode())+';unsigned char ssid[]='+json.dumps(ssid.decode())+';\n'
 fixture+='memcpy(b->Ssid,ssid,sizeof(ssid)-1);b->SsidLen=sizeof(ssid)-1;memcpy(b->PMK,expected,32);assert(wr_iot_precreated_key_matches(&ad,&dev,ssid,sizeof(ssid)-1,pass,sizeof(pass)-1));pass[0]^=1;assert(!wr_iot_precreated_key_matches(&ad,&dev,ssid,sizeof(ssid)-1,pass,sizeof(pass)-1));}\n'
fixture+='''{char hex[64];for(unsigned i=0;i<64;i++)hex[i]="0123456789abcdef"[i%16];for(unsigned i=0;i<32;i++)b->PMK[i]=(unsigned char)(((i*2)%16)*16+((i*2+1)%16));assert(wr_iot_precreated_key_matches(&ad,&dev,b->Ssid,b->SsidLen,hex,64));hex[63]='z';assert(!wr_iot_precreated_key_matches(&ad,&dev,b->Ssid,b->SsidLen,hex,64));}
puts("PASS actual vendor SHA1/HMAC/PBKDF matches4 independent vectors; requested passphrase/raw64 PMK matcher rejects wrong keys. Host injected BSS, not live identity/ownership proof.");return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-key-derivation-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+header+constants+functions+fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
print(json.dumps({'sources_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()},'vectors':len(vectors),'runtime_verified':False}))
