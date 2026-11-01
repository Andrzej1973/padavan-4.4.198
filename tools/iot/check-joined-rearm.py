#!/usr/bin/env python3
"""Execute extracted joined-rearm ordering with injected kernel operations."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("candidate",type=Path)
a=p.parse_args()
s=(a.candidate/"common/rtmp_init.c").read_text()
start=s.index("INT wr_iot_aux_family_retry_rearm_joined(")
brace=s.index("{",start);depth=1;end=brace+1
while depth:
 depth+=(s[end]=="{")-(s[end]=="}");end+=1
fn=s[start:end]
prefix=r"""
#include <assert.h>
#include <stdio.h>
#include "aux-family-retry-scheduler.h"
typedef int INT;typedef unsigned long ULONG;
#define EBUSY 16
#define WDEV_NUM_MAX 0
struct work_struct { int unused; };
typedef struct {
 struct work_struct wr_iot_aux_family_retry_work;
 int wr_iot_transition_lock;
 struct { int retiring; } wr_iot_transition;
 struct wr_iot_aux_retry_owner wr_iot_aux_family_retry;
 struct wr_iot_interface_ref wr_iot_interface_refs[1];
 struct wr_iot_family_close wr_iot_family_close[1];
} RTMP_ADAPTER;
static int held,flushed,busy,accept,schedules;
#define RTMP_IRQ_LOCK(lock,flags) do { (void)(lock);(flags)=0;assert(!held&&flushed);held=1; } while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do { (void)(lock);(void)(flags);assert(held);held=0; } while(0)
static void flush_work(struct work_struct *work){(void)work;assert(!held);flushed=1;}
static int work_busy(struct work_struct *work){(void)work;assert(held);return busy;}
static int schedule_work(struct work_struct *work){(void)work;assert(held);schedules++;return accept;}
static struct wr_iot_interface_ref *wr_iot_registry_find(struct wr_iot_interface_ref *r,unsigned int count,const void *dev,unsigned long generation){
 assert(held&&count==1);return r->device==dev&&r->generation==generation?r:0;
}
"""
suffix=r"""
static void setup(RTMP_ADAPTER *ad,int *dev){
 struct wr_iot_interface_ref *r=&ad->wr_iot_interface_refs[0];
 struct wr_iot_family_close *s=&ad->wr_iot_family_close[0];
 *ad=(RTMP_ADAPTER){0};held=flushed=busy=schedules=0;accept=1;
 wr_iot_ref_init(r,dev,1);wr_iot_family_close_init(s);
 r->published=1;r->phase=WR_REF_CLOSING;r->family=WR_REF_FAMILY_APCLI;
 r->close_stage=1;r->close_serial=3;r->close_epoch=2;r->last_token=4;
 s->device=dev;s->generation=1;s->serial=3;s->epoch=2;s->token=4;
 s->family=WR_REF_FAMILY_APCLI;s->phase=WR_FAMILY_DOWN_RETRY;
 wr_iot_aux_retry_init(&ad->wr_iot_aux_family_retry);
 assert(wr_iot_aux_retry_queue(&ad->wr_iot_aux_family_retry,r,s,1,1,1));
 assert(wr_iot_aux_retry_schedule_result(&ad->wr_iot_aux_family_retry,0));
}
int main(void){
 RTMP_ADAPTER ad;int dev;
 assert(wr_iot_aux_family_retry_rearm_joined(0)==-EBUSY);
 setup(&ad,&dev);assert(wr_iot_aux_family_retry_rearm_joined(&ad)==0&&schedules==1&&!held);
 setup(&ad,&dev);ad.wr_iot_transition.retiring=1;
 assert(wr_iot_aux_family_retry_rearm_joined(&ad)==-EBUSY&&!schedules);
 setup(&ad,&dev);busy=1;assert(wr_iot_aux_family_retry_rearm_joined(&ad)==-EBUSY&&!schedules);
 setup(&ad,&dev);ad.wr_iot_interface_refs[0].generation++;
 assert(wr_iot_aux_family_retry_rearm_joined(&ad)==-EBUSY&&!schedules);
 setup(&ad,&dev);accept=0;assert(wr_iot_aux_family_retry_rearm_joined(&ad)==-EBUSY&&schedules==1);
 assert(ad.wr_iot_aux_family_retry.phase==WR_AUX_RETRY_RETAINED&&ad.wr_iot_aux_family_retry.netdev_held);
 puts("PASS extracted joined rearm lock order, refusal gates and failed submission retention");
}
"""
with tempfile.TemporaryDirectory(prefix="wr-joined-rearm-") as directory:
 root=Path(directory);source=root/"check.c";binary=root/"check";source.write_text(prefix+fn+suffix)
 subprocess.run(["gcc","-std=c11","-Wall","-Wextra","-Werror","-fsanitize=address,undefined","-I"+str(a.candidate/"include"),str(source),"-o",str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
