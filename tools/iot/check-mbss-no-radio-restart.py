#!/usr/bin/env python3
"""Execute pinned vendor virtual UP/DOWN dispatcher with injected hardware hooks."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',type=Path);a=p.parse_args()
f=a.driver/'common/cmm_cfg.c';raw=f.read_bytes();s=raw.decode()
start=s.index('\t\tcase CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP:')
end=s.index('\t\tcase CMD_RTPRIV_IOCTL_VIRTUAL_INF_GET:',start)
body=s[start:end]
assert body.count('pInfConf->rt28xx_open(pAd->net_dev)')==1
assert body.count('pInfConf->rt28xx_close(pAd->net_dev)')==1
code=r'''
#include <assert.h>
#include <stdio.h>
#define CONFIG_AP_SUPPORT 1
#define CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP 1
#define CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN 2
#define NDIS_STATUS_FAILURE -1
#define DBGPRINT(level,args) ((void)0)
#define IN
#define VOID void
#define VIRTUAL_IF_NUM(ad) ((ad)->count)
#define VIRTUAL_IF_INC(ad) (++(ad)->count)
#define VIRTUAL_IF_DEC(ad) (--(ad)->count)
typedef struct adapter {unsigned count;void *net_dev;} RTMP_ADAPTER,*PRTMP_ADAPTER;
typedef struct {int(*rt28xx_open)(void*);void(*rt28xx_close)(void*);} RT_CMD_INF_UP_DOWN;
static unsigned opens,closes,make,update;
static int open_radio(void *dev){(void)dev;opens++;return 0;}
static void close_radio(void *dev){(void)dev;closes++;}
void APMakeAllBssBeacon(PRTMP_ADAPTER ad){assert(ad->count);make++;}
void APUpdateAllBeaconFrame(PRTMP_ADAPTER ad){assert(ad->count);update++;}
static int dispatch(PRTMP_ADAPTER pAd,int command,void *pData){switch(command){
'''+body+r'''
}return 0;}
int main(void){
 RTMP_ADAPTER ad={.count=2};RT_CMD_INF_UP_DOWN callbacks={open_radio,close_radio};
 for(unsigned n=0;n<1000;n++){
  assert(!dispatch(&ad,1,&callbacks));assert(ad.count==3);
  assert(!dispatch(&ad,2,&callbacks));assert(ad.count==2);
 }
 assert(!opens&&!closes&&make==1000&&update==1000);
 /* Main only also retains physical owner. Last-reference path is distinct. */
 ad.count=1;assert(!dispatch(&ad,1,&callbacks)&&ad.count==2&&!opens);
 assert(!dispatch(&ad,2,&callbacks)&&ad.count==1&&!closes);
 assert(!dispatch(&ad,2,&callbacks)&&!ad.count&&closes==1);
 assert(!dispatch(&ad,1,&callbacks)&&ad.count==1&&opens==1);
 puts("PASS actual vendor dispatcher:1000 third-reference UP/DOWN cycles retain Main+Guest, no physical open/close hook; last-reference close and first-reference open remain distinct. Beacon/hardware hooks injected; no association/runtime proof.");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mbss-norestart-') as td:
 path=Path(td)/'check.c';path.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(path),'-o',td+'/check'],check=True)
 result=subprocess.check_output([td+'/check'],text=True).strip()
print(json.dumps({'source':'common/cmm_cfg.c','source_sha256':hashlib.sha256(raw).hexdigest(),
 'extracted_sha256':hashlib.sha256(body.encode()).hexdigest(),'host_result':result,
 'scope':'Vendor reference dispatcher only, not current candidate composition, beacon descendants, concurrency, dynamic credentials or isolation.',
 'runtime_verified':False},indent=2))
