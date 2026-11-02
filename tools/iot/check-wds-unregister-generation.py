#!/usr/bin/env python3
"""Exercise actual generation capture and stale post-unregister receipt."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
s=(a.candidate/'ap/ap_wds.c').read_text();start=s.index('            /* Snapshot before unregister while RTNL pins the device. */');end=s.index('\t\t\tRtmpOSNetDevDetach(wdev->if_dev);',start);capture=s[start:end]
assert 'wr_generation, 1);' in s
code=r'''
#include "interface-registry.h"
#include <assert.h>
typedef unsigned int UINT;typedef unsigned long ULONG;
#define WDEV_NUM_MAX 1
#define NDIS_STATUS_FAILURE -1
struct wifi_dev {void *if_dev;};
struct adapter {int wr_iot_transition_lock;struct wr_iot_interface_ref wr_iot_interface_refs[2];};
static int held,protected=1;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static void RtmpOSNetDevProtect(int on){assert(!held);protected=on;}
static int snapshot(struct adapter *pAd,struct wifi_dev *wdev,unsigned long *saved){unsigned long wr_generation;
'''+capture+r'''
*saved=wr_generation;return 0;}
int main(void){struct adapter a={0};int device;struct wifi_dev w={&device};unsigned long saved=99;
struct wr_iot_interface_ref *r=&a.wr_iot_interface_refs[0];wr_iot_ref_init(r,&device,2);r->family=WR_REF_FAMILY_WDS;r->published=1;r->removing=1;r->last_token=1;r->close_stage=2;
assert(snapshot(&a,&w,&saved)==0&&saved==2&&!held&&protected);
r->generation=3;assert(!wr_iot_registry_after_unregister(r,&device,saved,1)&&!r->removal_stage);
r->generation=2;assert(wr_iot_registry_after_unregister(r,&device,saved,1)&&r->removal_stage==1);
protected=1;saved=99;assert(snapshot(&a,&w,&saved)==-1&&saved==99&&!protected&&!held);
r->removal_stage=0;r->close_stage=1;protected=1;assert(snapshot(&a,&w,&saved)==-1&&!protected);
return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-wds-generation-check-') as d:
 c=Path(d)/'check.c';c.write_text(code);subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True);subprocess.run([d+'/check'],check=True)
print('PASS captured generation, stale receipt refusal and pre-detach invalid state refusal')
