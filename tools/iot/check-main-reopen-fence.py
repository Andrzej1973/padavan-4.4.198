#!/usr/bin/env python3
"""Execute actual main-open reservation expression with live/retired owners."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
s=(a.candidate/'os/linux/rt_main_dev.c').read_text();start=s.index(' admitted = net_dev == adapter->net_dev &&');end=s.index(';',start)+1;admission=s[start:end]
assert 'wr_iot_main_recovery_allows_reopen(' in admission
assert '#include "wr-iot-main-reopen-admission.h"' in s.splitlines()
code=r'''
#include "wr-iot-main-reopen-admission.h"
#include "virtual-open-claim.h"
#include <assert.h>
#include <string.h>
#define WDEV_NUM_MAX 1
struct work_struct {unsigned int busy;};
struct net_device {int id;};
struct adapter {
 struct net_device *net_dev;
 struct wr_iot_main_recovery_owner wr_iot_main_recovery;
 struct work_struct wr_iot_main_recovery_work,wr_iot_aux_family_retry_work;
 struct {struct work_struct work;} wr_iot_main_recovery_reap_work;
 struct {unsigned int deferred_owners;} wr_iot_aux_family_retry;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX+1];
 unsigned int VirtualIfCnt;
};
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
static unsigned int work_busy(struct work_struct *w){return w->busy;}
static int reserve(struct adapter *adapter,struct net_device *net_dev){
 struct wr_iot_radio_ticket ticket;unsigned long generation=0;int admitted;
'''+admission+r'''
 return admitted;
}
static void ready(struct adapter *a,struct net_device *dev){
 *a=(struct adapter){0};a->net_dev=dev;
 wr_iot_main_recovery_init(&a->wr_iot_main_recovery);
 wr_iot_radio_transition_init(&a->wr_iot_transition);
 wr_iot_ref_init(&a->wr_iot_interface_refs[0],dev,1);
 a->wr_iot_interface_refs[0].family=WR_REF_FAMILY_MAIN;
 a->wr_iot_interface_refs[0].published=1;
}
static void refused_without_reservation(struct adapter *a,struct net_device *dev){
 struct wr_iot_radio_transition before;memcpy(&before,&a->wr_iot_transition,sizeof before);
 struct wr_iot_interface_ref refs[2];memcpy(refs,a->wr_iot_interface_refs,sizeof refs);
 assert(!reserve(a,dev));
 assert(!memcmp(&before,&a->wr_iot_transition,sizeof before));
 assert(!memcmp(refs,a->wr_iot_interface_refs,sizeof refs));
}
int main(void){struct adapter a;struct net_device dev={0};
 ready(&a,&dev);assert(reserve(&a,&dev));
 for(int phase=WR_MAIN_OWNER_QUEUED;phase<=WR_MAIN_OWNER_STOPPING;phase++){
  ready(&a,&dev);a.wr_iot_main_recovery.phase=phase;
  refused_without_reservation(&a,&dev);
 }
 ready(&a,&dev);a.wr_iot_main_recovery.deferred_owners=1;refused_without_reservation(&a,&dev);
 ready(&a,&dev);a.wr_iot_main_recovery.completed=1;a.wr_iot_main_recovery.module_pin_released=1;refused_without_reservation(&a,&dev);
 ready(&a,&dev);a.wr_iot_main_recovery.device=&dev;refused_without_reservation(&a,&dev);
 ready(&a,&dev);a.wr_iot_main_recovery_work.busy=1;refused_without_reservation(&a,&dev);
 ready(&a,&dev);a.wr_iot_main_recovery_reap_work.work.busy=2;refused_without_reservation(&a,&dev);
 a.wr_iot_main_recovery_reap_work.work.busy=0;assert(reserve(&a,&dev));
 ready(&a,&dev);a.wr_iot_aux_family_retry.deferred_owners=1;refused_without_reservation(&a,&dev);
 ready(&a,&dev);a.wr_iot_aux_family_retry_work.busy=2;refused_without_reservation(&a,&dev);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-main-reopen-check-') as d:
 c=Path(d)/'check.c';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual main reserve: retained/completed-before-reap/work-busy refusal without mutation; joined/fresh owner admitted')
