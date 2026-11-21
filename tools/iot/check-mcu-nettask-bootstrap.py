#!/usr/bin/env python3
"""Run actual nettask entry/exit, scheduler and MCU-only helper with mocked OS."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
net=(a.candidate/'os/linux/rt_rbus_pci_drv.c').read_text()
def function(signature):
 start=net.index(signature);return net[start:net.index('\n}',start)+2]
init=function('NDIS_STATUS RtmpNetTaskInit(');exit=function('INT RtmpNetTaskExit(');data_exit=function('INT wr_iot_nettask_data_exit(')
fields=sorted(set(re.findall(r'RTMP_OS_TASKLET_KILL\(&pObj->(\w+)\)',exit)))
callbacks=sorted(set(re.findall(r'WR_IOT_INIT_ONE\(pAd, &pObj->\w+, (\w+),',init)))
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "nettask-lane-owner.h"
typedef int INT;typedef int NDIS_STATUS;typedef unsigned long ULONG;typedef void VOID;
typedef struct {unsigned id;} RTMP_NET_TASK_STRUCT;
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define CONFIG_ANDES_SUPPORT 1
#define CONFIG_AP_SUPPORT 1
#define CONFIG_ATE 1
#define DFS_SUPPORT 1
#define UAPSD_SUPPORT 1
#define HIF_MT 1
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE -1
#define IF_DEV_CONFIG_OPMODE_ON_AP(ad) if(1)
'''
prefix+='struct cookie {'+''.join('RTMP_NET_TASK_STRUCT '+f+';' for f in fields)+'};typedef struct cookie *POS_COOKIE;\n'
prefix+=r'''
typedef struct {
 void *OS_Cookie;struct {int hif_type;} chipCap;int is7603;
 int wr_iot_nettask_lock,wr_iot_nettask_wait;
 unsigned wr_iot_nettask_joined,wr_iot_nettask_initializing,wr_iot_nettask_release_claimed;
 unsigned wr_iot_nettask_data_joined,wr_iot_nettask_data_joining;
 unsigned wr_iot_boot_active,wr_iot_boot_mcu_only;
 struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner,wr_iot_nettask_data_owner;
} RTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->is7603)
static unsigned held,created[64],killed[64],scheduled[64],init_calls,owned_calls,drift,fail_init,owned,nest;
static int nested_exit;
static RTMP_ADAPTER *current;
static int initialize(RTMP_NET_TASK_STRUCT *,void (*)(unsigned long),unsigned long);
static void kill_task(RTMP_NET_TASK_STRUCT *);
static void schedule(RTMP_NET_TASK_STRUCT *);
#define RTMP_INT_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define RTMP_OS_TASKLET_INIT(ad,t,f,data) ((void)(ad),initialize(t,f,data))
#define RTMP_OS_TASKLET_KILL(t) kill_task(t)
#define RTMP_OS_TASKLET_SCHE(t) schedule(t)
#define in_atomic() 0
#define irqs_disabled() 0
#define msecs_to_jiffies(n) (n)
#define wait_event_timeout(q,c,t) ((void)(q),assert(!held&&(t)==5000),(c)?1:0)
#define wake_up_all(q) ((void)(q))
static int wr_iot_mcu_boot_owned(RTMP_ADAPTER *ad){assert(ad==current&&!held);owned_calls++;return owned&&owned_calls!=drift;}
'''
prefix+='\n'.join('static void '+f+'(unsigned long data){(void)data;}' for f in callbacks)+'\n'
prefix+=(a.candidate/'include/wr-iot-nettask-data-drain.inc').read_text()+'\n'
prefix+=(a.candidate/'include/wr-iot-nettask-schedule.inc').read_text().replace('#include "wr-iot-nettask-data-drain.inc"','')+'\n'
restart_layer='INT wr_iot_nettask_boot_rx_restart(' in (a.candidate/'include/wr-iot-mcu-nettask-bootstrap.inc').read_text()
if restart_layer:
 prefix+='static unsigned restart_owned;static int wr_iot_mcu_boot_rx_restart_owned(RTMP_ADAPTER *ad){assert(ad==current&&!held);owned_calls++;return restart_owned&&owned_calls!=drift;}\n'
prefix+=(a.candidate/'include/wr-iot-mcu-nettask-bootstrap.inc').read_text()+'\n'+init+'\n'+exit+'\n'+data_exit
prefix+=r'''
static void schedule(RTMP_NET_TASK_STRUCT *t){assert(!held&&created[t->id]>killed[t->id]);scheduled[t->id]++;}
static int initialize(RTMP_NET_TASK_STRUCT *t,void (*fn)(unsigned long),unsigned long data){
 assert(!held&&fn&&data==(unsigned long)current);init_calls++;
 if(init_calls==fail_init)return 0;
 created[t->id]++;
 wr_iot_nettask_schedule(current,t); /* Publication must still be barred. */
 if(nest){nest=0;nested_exit=RtmpNetTaskExit(current);}
 return 1;
}
static void kill_task(RTMP_NET_TASK_STRUCT *t){
 assert(!held&&created[t->id]>killed[t->id]);killed[t->id]++;
 wr_iot_nettask_schedule(current,t); /* Late rearm must remain barred. */
}
static void fresh(RTMP_ADAPTER *ad,struct cookie *cookie){
 memset(ad,0,sizeof(*ad));memset(cookie,0,sizeof(*cookie));current=ad;
 ad->OS_Cookie=cookie;ad->is7603=ad->chipCap.hif_type=1;
 ad->wr_iot_boot_active=ad->wr_iot_nettask_release_claimed=1;
 ad->wr_iot_nettask_joined=ad->wr_iot_nettask_data_joined=1;
 wr_iot_tasklet_schedule_init(&ad->wr_iot_nettask_owner);wr_iot_tasklet_schedule_init(&ad->wr_iot_nettask_data_owner);
 memset(created,0,sizeof(created));memset(killed,0,sizeof(killed));memset(scheduled,0,sizeof(scheduled));
 init_calls=owned_calls=drift=fail_init=nest=0;owned=1;
'''
prefix+='\n'.join('cookie->'+f+'.id='+str(i+1)+';' for i,f in enumerate(fields))+'\n}\n'
tail=r'''
int main(void){
 RTMP_ADAPTER ad;struct cookie cookie;
 fresh(&ad,&cookie);nest=1;
 assert(RtmpNetTaskInit(&ad)==0&&nested_exit==-1&&init_calls==2&&ad.wr_iot_boot_mcu_only);
 assert(!ad.wr_iot_nettask_owner.blocked&&ad.wr_iot_nettask_data_owner.blocked&&ad.wr_iot_nettask_release_claimed);
 assert(ad.wr_iot_nettask_data_joined&&!ad.wr_iot_nettask_joined&&!ad.wr_iot_nettask_initializing);
 assert(RtmpNetTaskInit(&ad)==-1&&init_calls==2);
 wr_iot_nettask_schedule(&ad,&cookie.rx1_done_task);wr_iot_nettask_schedule(&ad,&cookie.hcca_dma_done_task);
 wr_iot_nettask_schedule(&ad,&cookie.rx_done_task);
 assert(scheduled[cookie.rx1_done_task.id]==1&&scheduled[cookie.hcca_dma_done_task.id]==1&&!scheduled[cookie.rx_done_task.id]);
 assert(RtmpNetTaskExit(&ad)==0&&!ad.wr_iot_boot_mcu_only&&ad.wr_iot_nettask_joined);
 assert(killed[cookie.rx1_done_task.id]==1&&killed[cookie.hcca_dma_done_task.id]==1&&!killed[cookie.rx_done_task.id]);
 assert(RtmpNetTaskExit(&ad)==0&&!held);
 fresh(&ad,&cookie);owned=0;assert(RtmpNetTaskInit(&ad)==-1&&!init_calls);
 fresh(&ad,&cookie);drift=2;assert(RtmpNetTaskInit(&ad)==-1&&init_calls==2);
 assert(killed[cookie.rx1_done_task.id]==1&&killed[cookie.hcca_dma_done_task.id]==1);
 assert(ad.wr_iot_nettask_owner.blocked&&ad.wr_iot_nettask_data_owner.blocked&&!ad.wr_iot_nettask_initializing&&!ad.wr_iot_boot_mcu_only);
#ifdef OS_ABL_FUNC_SUPPORT
 for(unsigned fail=1;fail<=2;fail++){
  fresh(&ad,&cookie);fail_init=fail;
  assert(RtmpNetTaskInit(&ad)==-1&&!ad.wr_iot_boot_mcu_only&&!ad.wr_iot_nettask_initializing);
  assert(killed[cookie.rx1_done_task.id]==(fail==2?1:0)&&!killed[cookie.hcca_dma_done_task.id]);
 }
#endif
 fresh(&ad,&cookie);ad.wr_iot_nettask_data_owner.poisoned=1;assert(RtmpNetTaskInit(&ad)==-1&&!init_calls);
 fresh(&ad,&cookie);ad.wr_iot_boot_active=ad.wr_iot_nettask_release_claimed=0;
 assert(RtmpNetTaskInit(&ad)==0&&!ad.wr_iot_nettask_owner.blocked&&!ad.wr_iot_nettask_data_owner.blocked);
 assert(RtmpNetTaskExit(&ad)==0&&!held);
 puts("PASS actual nettask init/exit: MCU-only publication, data fence, partial init cleanup, stale ownership, nested exit refusal and ordinary path; OS joins injected");
}
'''
if restart_layer:
 anchor=' puts("PASS actual nettask init/exit:'
 pos=tail.index(anchor)
 tail=tail[:pos]+r'''
 fresh(&ad,&cookie);owned=0;restart_owned=1;
 assert(wr_iot_mcu_boot_rx_restart_owned(&ad));
 assert(RtmpNetTaskInit(&ad)==-1&&!init_calls);
 assert(wr_iot_nettask_boot_rx_restart(&ad)==0&&init_calls==2&&ad.wr_iot_boot_mcu_only);
 assert(ad.wr_iot_nettask_data_joined&&ad.wr_iot_nettask_data_owner.blocked&&ad.wr_iot_nettask_release_claimed);
 assert(RtmpNetTaskExit(&ad)==0&&!ad.wr_iot_boot_mcu_only);
 fresh(&ad,&cookie);owned=0;restart_owned=0;
 assert(wr_iot_nettask_boot_rx_restart(&ad)==-1&&!init_calls);
 fresh(&ad,&cookie);owned=0;restart_owned=1;drift=2;
 assert(wr_iot_nettask_boot_rx_restart(&ad)==-1&&init_calls==2&&!ad.wr_iot_boot_mcu_only);
 assert(killed[cookie.rx1_done_task.id]==1&&killed[cookie.hcca_dma_done_task.id]==1);
 restart_owned=0;
'''+tail[pos:]
with tempfile.TemporaryDirectory(prefix='wr-mcu-nettask-bootstrap-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+tail)
 for abl in (False,True):
  cmd=['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',td+'/check']
  if abl:cmd.insert(1,'-DOS_ABL_FUNC_SUPPORT=1')
  subprocess.run(cmd,check=True);subprocess.run([td+'/check'],check=True)
