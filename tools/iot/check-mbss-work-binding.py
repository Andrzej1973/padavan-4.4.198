#!/usr/bin/env python3
"""Exercise actual MBSS worker/owner control flow with injected backend results."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('--external-join',action='store_true');p.add_argument('--stop-join',action='store_true');a=p.parse_args();here=Path(__file__).resolve().parent
helper=(a.candidate/'include/wr-iot-mbss-recovery-work.inc').read_text()
assert 'RT_MOD_DEC_USE_COUNT' not in helper and 'dev_put(' not in helper
s=(a.candidate/'include/wr-iot-mbss-close-checked.inc').read_text();start=s.index('INT wr_iot_mbss_begin_close(');begin=s[start:s.index('\n}',start)+2]
header=(a.candidate/'include/rtmp.h').read_text();start=header.index('struct wr_iot_mbss_work_context {');context=header[start:header.index('\n};',start)+3]
for rel,call in [('include/wr-iot-peer-adapter-release.inc','wr_iot_mbss_recovery_idle_locked(pAd)'),('include/wr-iot-raw-recovery-free-fence.inc','wr_iot_mbss_recovery_idle_locked(ad)'),('os/linux/rt_main_dev.c','wr_iot_mbss_recovery_idle_locked(adapter)'),('include/wr-iot-mbss-open-admission.inc','wr_iot_mbss_recovery_idle_locked(adapter)'),('include/wr-iot-netdev-registration.inc','wr_iot_mbss_recovery_idle_locked(pAd)')]:assert call in (a.candidate/rel).read_text()
code=r'''
#include "mbss-recovery-storage.h"
#include <assert.h>
#include <stddef.h>
#define WDEV_NUM_MAX 1
#define MBSS_SUPPORT 1
#define TRUE 1
#define FALSE 0
#define VOID void
typedef int BOOLEAN;typedef unsigned int UINT;typedef unsigned long ULONG;typedef int INT;
typedef struct adapter RTMP_ADAPTER,*PRTMP_ADAPTER;
struct work_struct {unsigned int busy;};
struct device {RTMP_ADAPTER *ad;unsigned int refs;};typedef struct device *PNET_DEV;
'''+context+r'''
struct adapter {
 int wr_iot_transition_lock;unsigned int VirtualIfCnt;
 PNET_DEV net_dev;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[2];
 struct wr_iot_mbss_work_context wr_iot_mbss_work[2];
};
static int held,context_bad,backend_fail,backend_calls,module_refs;
static unsigned long last_serial;
#define container_of(p,t,m) ((t*)((char*)(p)-offsetof(t,m)))
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static unsigned int work_busy(struct work_struct *w){assert(held);return w->busy;}
static int wr_iot_os_join_context(void){return context_bad;}
'''+begin+r'''
/* Backend boundary mock: worker ownership/order is tested here; actual
 * checked executor, hardware side effects and kernel timing are separate. */
static int wr_iot_mbss_close_checked(PNET_DEV dev,unsigned long gen,const struct wr_iot_radio_ticket *ticket){
 RTMP_ADAPTER *ad=dev->ad;struct wr_iot_interface_ref *r=&ad->wr_iot_interface_refs[1];
 assert(!held&&module_refs==1&&dev->refs==1&&gen==r->generation);backend_calls++;last_serial=ticket->serial;
 if(r->phase==WR_REF_OWNED)assert(wr_iot_ref_begin_close(r,dev,gen,r->last_token));
 r->close_serial=ticket->serial;r->close_stage=2;
 if(backend_fail)return -1;
 assert(wr_iot_radio_finish(&ad->wr_iot_transition,ticket,1));
 assert(wr_iot_ref_consume(r,dev,gen,r->last_token));r->close_stage=4;
 ad->VirtualIfCnt--;module_refs--;return 0;
}
#include "wr-iot-mbss-recovery-work.inc"
static void ready(RTMP_ADAPTER *ad,struct device *main,struct device *dev){
 *ad=(RTMP_ADAPTER){0};*main=(struct device){ad,1};*dev=(struct device){ad,1};ad->net_dev=main;
 wr_iot_radio_transition_init(&ad->wr_iot_transition);ad->wr_iot_transition.phase=WR_RADIO_READY;ad->wr_iot_transition.main_ready=1;ad->VirtualIfCnt=1;
 for(unsigned int i=0;i<2;i++){
  wr_iot_ref_init(&ad->wr_iot_interface_refs[i],0,0);wr_iot_mbss_recovery_init(&ad->wr_iot_mbss_recovery[i]);
  ad->wr_iot_mbss_work[i].adapter=ad;ad->wr_iot_mbss_work[i].slot=i;
 }
 struct wr_iot_interface_ref *r=&ad->wr_iot_interface_refs[1];wr_iot_ref_init(r,dev,1);r->family=WR_REF_FAMILY_MBSS;r->published=1;
 assert(wr_iot_ref_reserve(r,dev,1,7));assert(wr_iot_ref_open_finish(r,dev,1,7,1));
 held=context_bad=backend_fail=backend_calls=0;module_refs=1;last_serial=0;
}
static void queue(RTMP_ADAPTER *ad){assert(wr_iot_mbss_recovery_queue(&ad->wr_iot_mbss_recovery[1],&ad->wr_iot_interface_refs[1],&ad->wr_iot_transition,WR_MBSS_RECOVERY_OPEN_ACQUIRED,0,1,1));}
static void execute(RTMP_ADAPTER *ad){ad->wr_iot_mbss_work[1].work.busy=2;wr_iot_mbss_recovery_work_fn(&ad->wr_iot_mbss_work[1].work);ad->wr_iot_mbss_work[1].work.busy=0;assert(!held);}
static int idle(RTMP_ADAPTER *ad){int result;held=1;result=wr_iot_mbss_recovery_idle_locked(ad);held=0;return result;}
int main(void){RTMP_ADAPTER ad;struct device main,dev;
 ready(&ad,&main,&dev);assert(idle(&ad));ad.wr_iot_mbss_work[0].work.busy=2;assert(!idle(&ad));ad.wr_iot_mbss_work[0].work.busy=0;
 queue(&ad);execute(&ad);assert(backend_calls==1&&module_refs==0&&ad.wr_iot_mbss_recovery[1].completed&&dev.refs==1&&!idle(&ad));
 assert(wr_iot_mbss_recovery_complete(&ad.wr_iot_mbss_recovery[1],1));assert(idle(&ad));
 ad.wr_iot_mbss_work[1].work.busy=2;assert(!idle(&ad));
 ready(&ad,&main,&dev);queue(&ad);backend_fail=1;execute(&ad);
 assert(ad.wr_iot_mbss_recovery[1].phase==WR_MBSS_OWNER_RETAINED&&module_refs==1&&dev.refs==1);
 unsigned long serial=last_serial;assert(wr_iot_mbss_recovery_requeue(&ad.wr_iot_mbss_recovery[1],3));backend_fail=0;execute(&ad);
 assert(backend_calls==2&&last_serial==serial&&module_refs==0&&ad.wr_iot_mbss_recovery[1].completed);
 ready(&ad,&main,&dev);queue(&ad);ad.wr_iot_interface_refs[1].generation++;execute(&ad);assert(!backend_calls&&module_refs==1&&ad.wr_iot_mbss_recovery[1].phase==WR_MBSS_OWNER_RETAINED);
 ready(&ad,&main,&dev);queue(&ad);context_bad=1;execute(&ad);assert(!backend_calls&&ad.wr_iot_mbss_recovery[1].phase==WR_MBSS_OWNER_QUEUED);
 ready(&ad,&main,&dev);queue(&ad);assert(wr_iot_mbss_recovery_request_stop(&ad.wr_iot_mbss_recovery[1]));execute(&ad);assert(!backend_calls&&module_refs==1);
 return 0;
}
'''
bound_gate=(a.candidate/'include/mbss-reaper-gate.h').exists()
if bound_gate:
 code=code.replace('#include "mbss-recovery-storage.h"','#include "mbss-recovery-storage.h"\n#include "mbss-reaper-gate.h"')
 code=code.replace(' int wr_iot_transition_lock;unsigned int VirtualIfCnt;', ' struct wr_iot_mbss_reaper_gate wr_iot_mbss_reaper_gate;\n int wr_iot_transition_lock;unsigned int VirtualIfCnt;')
 code=code.replace(' wr_iot_radio_transition_init(&ad->wr_iot_transition);', ' wr_iot_mbss_reaper_gate_init(&ad->wr_iot_mbss_reaper_gate);\n wr_iot_radio_transition_init(&ad->wr_iot_transition);')
if a.external_join or a.stop_join:
 marker='static void ready(RTMP_ADAPTER *ad,struct device *main,struct device *dev)'
 join_mock=r'''
static int flush_calls,put_calls,cancel_calls;
static void flush_work(struct work_struct *w){assert(!held);flush_calls++;w->busy=0;}
static void dev_put(PNET_DEV dev){assert(!held&&dev&&dev->refs==1);put_calls++;dev->refs--;}
'''
 join=((a.candidate/'include/wr-iot-mbss-recovery-join.inc') if bound_gate else (here/'mbss-recovery-join.inc')).read_text()
 if a.stop_join:
  join_mock+='static void cancel_work_sync(struct work_struct *w){assert(!held);cancel_calls++;w->busy=0;}\n'
  join+='\n'+((a.candidate/'include/wr-iot-mbss-recovery-stop.inc') if bound_gate else (here/'mbss-recovery-stop.inc')).read_text()
 code=code.replace(marker,join_mock+join+'\n'+marker)
 marker=' return 0;\n}\n'
 assert code.endswith(marker)
 tail=code.rindex(marker)
 code=code[:tail]+r'''
 ready(&ad,&main,&dev);queue(&ad);execute(&ad);flush_calls=put_calls=0;
 assert(wr_iot_mbss_recovery_join_completed(&ad)==0&&dev.refs==0&&put_calls==1&&flush_calls==2);
 assert(wr_iot_mbss_recovery_join_completed(&ad)==0&&put_calls==1);
 ready(&ad,&main,&dev);queue(&ad);backend_fail=1;execute(&ad);put_calls=0;
 assert(wr_iot_mbss_recovery_join_completed(&ad)==-1&&dev.refs==1&&!put_calls);
 ready(&ad,&main,&dev);queue(&ad);execute(&ad);ad.wr_iot_interface_refs[1].generation++;put_calls=0;
 assert(wr_iot_mbss_recovery_join_completed(&ad)==-1&&dev.refs==1&&!put_calls);
 for(int fault=0;fault<5;fault++){
  ready(&ad,&main,&dev);queue(&ad);execute(&ad);put_calls=0;
  if(fault==0)ad.wr_iot_mbss_recovery[1].close_ticket_valid=0;
  if(fault==1)ad.wr_iot_mbss_recovery[1].close_ticket.serial++;
  if(fault==2)ad.wr_iot_interface_refs[1].published=0;
  if(fault==3)ad.wr_iot_interface_refs[1].removing=1;
  if(fault==4)ad.wr_iot_mbss_recovery[1].phase=WR_MBSS_OWNER_IDLE;
  assert(wr_iot_mbss_recovery_join_completed(&ad)==-1&&dev.refs==1&&!put_calls);
 }
 ready(&ad,&main,&dev);context_bad=1;flush_calls=0;
 assert(wr_iot_mbss_recovery_join_completed(&ad)==-1&&!flush_calls);
 return 0;
}
'''
if a.stop_join:
 marker=' return 0;\n}\n';tail=code.rindex(marker)
 code=code[:tail]+r'''
 ready(&ad,&main,&dev);queue(&ad);put_calls=0;
 assert(wr_iot_mbss_recovery_stop_join(&ad)==-1&&dev.refs==1&&!put_calls);
 assert(ad.wr_iot_mbss_recovery[1].stop_requested&&ad.wr_iot_mbss_recovery[1].phase==WR_MBSS_OWNER_STOPPING);
 execute(&ad);assert(!backend_calls&&module_refs==1);
 ready(&ad,&main,&dev);queue(&ad);execute(&ad);put_calls=0;
 assert(wr_iot_mbss_recovery_stop_join(&ad)==0&&dev.refs==0&&put_calls==1);
 ready(&ad,&main,&dev);context_bad=1;
 assert(wr_iot_mbss_recovery_stop_join(&ad)==-1&&!ad.wr_iot_mbss_recovery[1].stop_requested);
 return 0;
}
'''
if bound_gate and a.stop_join:
 marker=' return 0;\n}\n';tail=code.rindex(marker)
 code=code[:tail]+r'''
 ready(&ad,&main,&dev);flush_calls=put_calls=cancel_calls=0;
 assert(wr_iot_mbss_reaper_enter(&ad.wr_iot_mbss_reaper_gate));
 assert(wr_iot_mbss_recovery_join_completed(&ad)==-1&&!flush_calls&&!put_calls);
 assert(wr_iot_mbss_recovery_stop_join(&ad)==-1&&!cancel_calls&&!flush_calls);
 assert(ad.wr_iot_mbss_reaper_gate.stopped&&ad.wr_iot_mbss_reaper_gate.reaping);
 assert(wr_iot_mbss_reaper_leave(&ad.wr_iot_mbss_reaper_gate));
 assert(!wr_iot_mbss_submission_enter(&ad.wr_iot_mbss_reaper_gate));
 assert(wr_iot_mbss_recovery_stop_join(&ad)==0&&cancel_calls==2&&flush_calls==2);
 assert(!ad.wr_iot_mbss_reaper_gate.reaping&&ad.wr_iot_mbss_reaper_gate.stopped);
 ready(&ad,&main,&dev);flush_calls=cancel_calls=0;
 assert(wr_iot_mbss_submission_enter(&ad.wr_iot_mbss_reaper_gate));
 assert(wr_iot_mbss_recovery_join_completed(&ad)==-1&&!flush_calls);
 assert(wr_iot_mbss_recovery_stop_join(&ad)==-1&&!cancel_calls&&ad.wr_iot_mbss_reaper_gate.stopped);
 assert(wr_iot_mbss_submission_leave(&ad.wr_iot_mbss_reaper_gate));
 assert(wr_iot_mbss_recovery_stop_join(&ad)==0);
 assert(!wr_iot_mbss_submission_enter(&ad.wr_iot_mbss_reaper_gate));
 ready(&ad,&main,&dev);ad.wr_iot_mbss_reaper_gate.poisoned=1;flush_calls=cancel_calls=0;
 assert(wr_iot_mbss_recovery_join_completed(&ad)==-1&&!flush_calls);
 assert(wr_iot_mbss_recovery_stop_join(&ad)==-1&&!cancel_calls);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mbss-work-check-') as d:
 c=Path(d)/'check.c';c.write_text(code);subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',d+'/check'],check=True);subprocess.run([d+'/check'],check=True)
print('PASS actual MBSS work callback/owner flow, exact retry, stale/context/stop refusal and live-work fence; backend injected')
