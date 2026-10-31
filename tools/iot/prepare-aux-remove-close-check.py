#!/usr/bin/env python3
"""Extract actual APCLI/Monitor removes; inject failure at close completion."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
functions=[]
for name,sig in [('ap/ap_apcli.c','INT ApCli_Remove('),('sniffer/sniffer_radiotap.c','INT Monitor_Remove(')]:
 s=(a.candidate/name).read_text();start=s.index(sig);body=s[start:s.index('\n}',start)+2]
 assert body.index('RtmpOSNetDevClose(')<body.index('wr_iot_netdev_close_phase_idle(')<body.index('RtmpOSNetDevDetach(')
 functions.append(body)
prefix=r'''
#include "interface-reference.h"
#include <assert.h>
#include <string.h>
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define FALSE 0
#define MAX_APCLI_NUM 2
typedef int INT;typedef unsigned int UINT;
typedef unsigned long ULONG;typedef void *PNET_DEV;
#define WDEV_NUM_MAX 0
struct wifi_dev{void *if_dev;};
typedef struct{struct{struct{struct wifi_dev wdev;} ApCliTab[2];} ApCfg;
 struct{struct wifi_dev monitor_wdev;int monitor_initiated;}monitor_ctrl;int flg_apcli_init;
 int wr_iot_transition_lock;unsigned int wr_iot_registration_inflight;
 struct wr_iot_interface_ref wr_iot_interface_refs[1];}RTMP_ADAPTER;
static int protected,mark_ok,close_ok,marks,closes,detaches,frees,unregs;
static int locked;static RTMP_ADAPTER *current;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!locked);locked=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(locked);locked=0;}while(0)
static int mark(RTMP_ADAPTER *a,void *d){assert(d&&!protected);marks++;
 if(mark_ok){struct wr_iot_interface_ref *r=&a->wr_iot_interface_refs[0];
 wr_iot_ref_init(r,d,1);r->published=r->removing=1;r->phase=WR_REF_OWNED;}
 return mark_ok?0:1;}
static void protect(int on){assert(protected!=on);protected=on;}
static void close_dev(void *d){assert(d&&protected&&!locked);closes++;
 if(close_ok)current->wr_iot_interface_refs[0].phase=WR_REF_IDLE;}
static void detach(void *d){assert(d&&protected&&close_ok);detaches++;}
static void unreg(RTMP_ADAPTER *a,struct wifi_dev *w){(void)a;assert(w->if_dev&&!protected&&close_ok);unregs++;}
static void free_dev(void *d){assert(d&&!protected&&close_ok);frees++;}
#define wr_iot_netdev_mark_removing(a,d) mark(a,d)
#define RtmpOSNetDevProtect(on) protect(on)
#define RtmpOSNetDevClose(d) close_dev(d)
#define RtmpOSNetDevDetach(d) detach(d)
#define rtmp_wdev_idx_unreg(a,w) unreg(a,w)
#define RtmpOSNetDevFree(d) free_dev(d)
'''
post=r'''
int main(void){RTMP_ADAPTER a;int dev;
 for(int monitor=0;monitor<2;monitor++){
  memset(&a,0,sizeof a);current=&a;protected=marks=closes=detaches=frees=unregs=0;
  struct wifi_dev *w=monitor?&a.monitor_ctrl.monitor_wdev:&a.ApCfg.ApCliTab[0].wdev;
  w->if_dev=&dev;mark_ok=0;close_ok=0;
  assert((monitor?Monitor_Remove(&a):ApCli_Remove(&a))==1);
  assert(marks==1&&!closes&&!detaches&&!frees&&!protected&&w->if_dev==&dev);
  mark_ok=1;
  assert((monitor?Monitor_Remove(&a):ApCli_Remove(&a))==1);
  assert(closes==1&&!detaches&&!frees&&!unregs&&!protected&&w->if_dev==&dev);
  /* Success branch only verifies ordering. These mocks do not establish
   * callback quiescence or make the subsequent free production-safe. */
  close_ok=1;
  assert((monitor?Monitor_Remove(&a):ApCli_Remove(&a))==0);
  assert(closes==2&&detaches==1&&frees==1&&unregs==1&&!protected&&!w->if_dev);
 }
 assert(!locked);return 0;}
'''
registration=(a.candidate/'include/wr-iot-netdev-registration.inc').read_text()
start=registration.index('INT wr_iot_netdev_close_phase_idle(')
helper=registration[start:registration.index('\n}',start)+2]
a.output.write_text(prefix+helper+'\n'+'\n'.join(functions)+post,encoding='utf-8')
print('Extracted two removes and actual close-phase helper; RTNL/close/free mocked, no callback lifetime proof')
