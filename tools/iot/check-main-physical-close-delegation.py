#!/usr/bin/env python3
"""Exercise actual ndo_stop/VERIFY handoff, owner refs and physical worker."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
source=(a.candidate/'os/linux/rt_main_dev.c').read_text()
def function(signature):
 start=source.index(signature);end=source.index('\n}',start)+2;return source[start:end]
submit=function('static int wr_iot_main_verify_recovery_submit(')
start=source.index('  struct wr_iot_radio_ticket close_ticket;',source.index('int MainVirtualIF_open('));end=source.index('  return -1;',start)+len('  return -1;');verify=source[start:end]
assert 'close_ticket.operation != WR_RADIO_CLOSE &&' in verify
with tempfile.TemporaryDirectory(prefix='wr-main-close-delegation-') as d:
 c=Path(d)/'check.c';subprocess.run(['python3',str(here/'prepare-main-close-check.py'),str(c),'--candidate',str(a.candidate)],check=True)
 s=c.read_text();s=s[:s.index('int main(void)')]
 s=s.replace('#include "main-open-recovery-owner.h"','#include "main-open-recovery-owner.h"\n#include "pci-retirement-owner.h"')
 s=s.replace('struct net_device { PRTMP_ADAPTER priv; };','struct net_device { PRTMP_ADAPTER priv;int refs; };\nstruct work_struct {int pending;};\nstruct delayed_work {struct work_struct work;};')
 s=s.replace(' int wr_iot_ticket_wait;', ''' int wr_iot_ticket_wait;
 struct wr_iot_pci_retirement wr_iot_pci_retirement;
 struct work_struct wr_iot_main_recovery_work;
 struct delayed_work wr_iot_main_recovery_reap_work;''')
 marker='static int held,pins,preclose,down_calls,down_result,wakes;'
 s=s.replace(marker,marker+'''
#define HZ 100
#define RT_DEBUG_ERROR 1
#define DBGPRINT(a,b) ((void)0)
static int rtnl=1,work_accept=1,reaper_accept=1;
static int uncertain_finish;
static int finish_preclose(struct wr_iot_interface_ref *r,const struct wr_iot_radio_ticket *t){
 if(uncertain_finish)return 0;
 return wr_iot_main_close_finish_preclose(r,t);
}
#define wr_iot_main_close_finish_preclose finish_preclose
static void rtnl_unlock(void){assert(rtnl&&!held&&pins>0);rtnl=0;}
static void dev_hold(struct net_device *dev){assert(rtnl&&!held);dev->refs++;}
static void dev_put(struct net_device *dev){assert(dev->refs>0&&!held);dev->refs--;}
static int schedule_work(struct work_struct *w){assert(held);w->pending=work_accept;return work_accept;}
static int schedule_delayed_work(struct delayed_work *w,int delay){assert(held&&delay>0);w->work.pending=reaper_accept;return reaper_accept;}
''')
 s=s.replace('assert(ad&&ticket&&!held);down_calls++;','assert(ad&&ticket&&!held);assert(ticket->operation!=WR_RADIO_CLOSE||!rtnl);down_calls++;')
 marker='static int wr_iot_main_close_continue_checked(';assert s.count(marker)==1;s=s.replace(marker,submit+'\n'+marker)
 s+='\nstatic int failed_verify(PRTMP_ADAPTER adapter,struct net_device *net_dev,unsigned long generation){\n'+verify+'\n}\n'
 s+=r'''
static void fresh(struct adapter *ad,struct net_device *dev,int *peer){
 *ad=(struct adapter){0};*dev=(struct net_device){0};pins=0;down_result=0;setup(ad,dev,peer,1);
 rtnl=1;down_calls=preclose=0;work_accept=reaper_accept=1;uncertain_finish=0;
}
int main(void){struct adapter ad;struct net_device dev;int peer,released;
 fresh(&ad,&dev,&peer);assert(MainVirtualIF_close(&dev)==0);
 assert(!down_calls&&pins==1&&dev.refs==1&&preclose==1&&rtnl);
 assert(ad.wr_iot_main_recovery.deferred_owners==1);
 assert(wr_iot_main_recovery_execute(&ad,&released)==0&&released&&!rtnl);
 assert(down_calls==1&&pins==0&&dev.refs==1);
 assert(wr_iot_main_recovery_complete(&ad.wr_iot_main_recovery,1));dev_put(&dev);
 fresh(&ad,&dev,&peer);pins=0;setup(&ad,&dev,&peer,2);
 assert(MainVirtualIF_close(&dev)==0&&down_calls==1&&pins==0&&dev.refs==0&&rtnl);
 fresh(&ad,&dev,&peer);assert(MainVirtualIF_close(&dev)==0);down_result=1;
 assert(wr_iot_main_recovery_execute(&ad,&released)==-1&&released&&!rtnl&&pins==1&&dev.refs==1);
 assert(wr_iot_main_recovery_requeue(&ad.wr_iot_main_recovery,3,1));
 assert(wr_iot_main_recovery_schedule_result(&ad.wr_iot_main_recovery,1));
 rtnl=1;down_result=0;
 assert(wr_iot_main_recovery_execute(&ad,&released)==0&&released&&!rtnl&&pins==0);
 fresh(&ad,&dev,&peer);assert(failed_verify(&ad,&dev,1)==-1);
 assert(!down_calls&&pins==1&&dev.refs==1);
 assert(wr_iot_main_recovery_execute(&ad,&released)==0&&released&&!rtnl&&pins==0);
 fresh(&ad,&dev,&peer);ad.wr_iot_transition.retiring=1;ad.wr_iot_pci_retirement.phase=WR_PCI_RETIRE_DRAINING;
 assert(MainVirtualIF_close(&dev)==0&&ad.wr_iot_main_recovery.deferred_owners==1&&!down_calls&&dev.refs==1);
 fresh(&ad,&dev,&peer);ad.wr_iot_transition.retiring=1;ad.wr_iot_pci_retirement.phase=WR_PCI_RETIRE_WORK_JOINED;
 assert(MainVirtualIF_close(&dev)==-1&&!ad.wr_iot_main_recovery.deferred_owners&&dev.refs==0&&pins==1&&!down_calls);
 fresh(&ad,&dev,&peer);
 {struct wr_iot_radio_ticket busy;
  assert(wr_iot_radio_begin(&ad.wr_iot_transition,ad.wr_iot_transition.epoch,WR_RADIO_VERIFY,&busy));
  assert(MainVirtualIF_close(&dev)==-1&&ad.wr_iot_main_recovery.deferred_owners==1&&dev.refs==1&&!down_calls&&pins==1);
  assert(wr_iot_radio_finish(&ad.wr_iot_transition,&busy,1));
  assert(wr_iot_main_recovery_execute(&ad,&released)==0&&released&&!rtnl&&pins==0);
 }
 fresh(&ad,&dev,&peer);uncertain_finish=1;
 assert(MainVirtualIF_close(&dev)==-1&&ad.wr_iot_main_recovery.deferred_owners==1&&dev.refs==1&&pins==1&&!down_calls);
 assert(ad.wr_iot_main_recovery.source==WR_MAIN_RECOVERY_CLOSE_UNCERTAIN);
 assert(wr_iot_main_recovery_execute(&ad,&released)==-1&&!released&&rtnl&&pins==1&&!down_calls&&preclose==1);
 fresh(&ad,&dev,&peer);work_accept=0;assert(MainVirtualIF_close(&dev)==0);
 assert(ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_RETAINED&&dev.refs==1&&pins==1&&!down_calls);
 fresh(&ad,&dev,&peer);reaper_accept=0;assert(MainVirtualIF_close(&dev)==-1);
 assert(ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_QUEUED&&dev.refs==1&&pins==1&&!down_calls);
 return 0;
}
'''
 c.write_text(s);subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',d+'/check'],check=True);subprocess.run([d+'/check'],check=True)
print('PASS actual ndo_stop/VERIFY deferred physical close, exact worker ticket, pin lifetime, PCI drain-only origin and queue failures')
