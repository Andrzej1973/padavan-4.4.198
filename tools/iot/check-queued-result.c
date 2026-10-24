/* Deterministic state/order checks; no real kernel concurrency claim. */
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define WR_IOT_RESULT_TEST
#define GFP_KERNEL 0
#define container_of(ptr,type,member) ((type *)((char *)(ptr)-offsetof(type,member)))
struct kref {int refs;};
typedef int spinlock_t;
struct completion {int signals;};
static int live,fail_alloc;
static void *kzalloc(size_t n,int flags){
 void *p;(void)flags;if(fail_alloc)return NULL;p=calloc(1,n);if(p)live++;return p;
}
static void kfree(void *p){assert(p&&live>0);live--;free(p);}
static void kref_init(struct kref *r){r->refs=1;}
static void kref_get(struct kref *r){assert(r->refs>0);r->refs++;}
static void kref_put(struct kref *r,void (*release)(struct kref *)){
 assert(r->refs>0);if(!--r->refs)release(r);
}
static void spin_lock_init(spinlock_t *l){*l=0;}
#define spin_lock_irqsave(l,f) ((f)=0,assert(!*(l)),*(l)=1)
#define spin_unlock_irqrestore(l,f) ((void)(f),assert(*(l)),*(l)=0)
static void init_completion(struct completion *c){c->signals=0;}
static void complete_all(struct completion *c){c->signals++;}
#include "queued-result.h"
typedef struct cmd {unsigned int command;int CmdFromNdis;void *buffer;size_t bufferlength;} *PCmdQElmt;
typedef int NDIS_STATUS;
typedef unsigned int NDIS_OID;
typedef void *PVOID;
typedef unsigned int UINT32;
typedef void *PRTMP_ADAPTER;
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define NDIS_STATUS_RESOURCES 2
#include "queued-work.h"
static struct cmd queued;
static struct wr_iot_queue_envelope copied;
static int reject_queue,operation_calls,cancel_during_work,immediate;
static int execute_test(PRTMP_ADAPTER ad){
 assert(ad==&queued);operation_calls++;
 if(cancel_during_work)wr_iot_result_cancel(copied.result);
 return 0;
}
NDIS_STATUS wr_iot_enqueue_internal_cmd(PRTMP_ADAPTER ad,NDIS_OID oid,PVOID buffer,UINT32 size){
 assert(ad==&queued&&oid==WR_IOT_CMD_QUEUED_RADIO&&size==sizeof(copied));
 if(reject_queue)return 1;
 memcpy(&copied,buffer,sizeof(copied));
 queued.command=oid;queued.CmdFromNdis=0;queued.buffer=&copied;queued.bufferlength=size;
 if(immediate){wr_iot_queue_dispatch(ad,&queued,execute_test);wr_iot_queue_cleanup(&queued);}
 return 0;
}
int main(void){
 struct wr_iot_queued_result *r;int status;
 fail_alloc=1;assert(!wr_iot_result_alloc()&&!live);fail_alloc=0;
 /* Enqueue failure: reserved queue ref and caller ref both released. */
 r=wr_iot_result_alloc();wr_iot_result_get(r);wr_iot_result_put(r);
 assert(live==1);wr_iot_result_put(r);assert(!live);
 /* Queued timeout/shutdown: caller leaves before worker sees cancellation. */
 r=wr_iot_result_alloc();wr_iot_result_get(r);
 assert(wr_iot_result_cancel(r)&&!wr_iot_result_cancel(r));
 assert(r->done.signals==1);wr_iot_result_put(r);assert(live==1);
 assert(!wr_iot_result_start(r)&&!wr_iot_result_finish(r,0));
 assert(wr_iot_result_read(r,&status)==WR_IOT_WORK_CANCELLED&&status==-1);
 wr_iot_result_put(r);assert(!live);
 /* Running timeout is uncertain; late success cannot overwrite it. */
 r=wr_iot_result_alloc();wr_iot_result_get(r);assert(wr_iot_result_start(r));
 assert(!wr_iot_result_start(r)&&wr_iot_result_cancel(r));wr_iot_result_put(r);
 assert(live==1&&!wr_iot_result_finish(r,0)&&r->done.signals==1);
 assert(wr_iot_result_read(r,&status)==WR_IOT_WORK_UNCERTAIN&&status==-1);
 wr_iot_result_put(r);assert(!live);
 /* Worker finishes first; late cancellation preserves terminal result. */
 for(int result=0;result<2;result++){
  r=wr_iot_result_alloc();wr_iot_result_get(r);assert(wr_iot_result_start(r));
  assert(wr_iot_result_finish(r,result)&&!wr_iot_result_finish(r,0));
  wr_iot_result_put(r);assert(live==1&&!wr_iot_result_cancel(r));
  assert(wr_iot_result_read(r,&status)==WR_IOT_WORK_DONE&&status==result);
  assert(r->done.signals==1);wr_iot_result_put(r);assert(!live);
 }
 /* Actual cleanup helper: unrelated/malformed entries do not consume refs;
  * internal accepted envelope cancels and drops exactly its queue reference. */
 {
  struct cmd cmd;struct wr_iot_queue_envelope e;
  r=wr_iot_result_alloc();wr_iot_result_get(r);e.result=r;
  cmd.command=0;cmd.CmdFromNdis=0;cmd.buffer=&e;cmd.bufferlength=sizeof(e);
  wr_iot_queue_cleanup(&cmd);assert(e.result==r&&r->refs.refs==2);
  cmd.command=WR_IOT_CMD_QUEUED_RADIO;cmd.CmdFromNdis=1;
  wr_iot_queue_cleanup(&cmd);assert(r->refs.refs==2);
  cmd.CmdFromNdis=0;cmd.bufferlength=0;
  wr_iot_queue_cleanup(&cmd);assert(r->refs.refs==2);
  cmd.bufferlength=sizeof(e);wr_iot_queue_cleanup(&cmd);
  assert(!e.result&&r->refs.refs==1&&r->done.signals==1);
  wr_iot_queue_cleanup(&cmd);assert(r->refs.refs==1);
  assert(wr_iot_result_read(r,&status)==WR_IOT_WORK_CANCELLED);
  wr_iot_result_put(r);assert(!live);
 }
 /* Producer and worker ownership, including worker completing before submit returns. */
 reject_queue=1;assert(wr_iot_queue_submit(&queued,&r)==1&&!r&&!live);
 reject_queue=0;fail_alloc=1;
 assert(wr_iot_queue_submit(&queued,&r)==2&&!r&&!live);fail_alloc=0;
 for(int mode=0;mode<5;mode++){
  operation_calls=0;cancel_during_work=mode==3;immediate=mode==4;
  assert(!wr_iot_queue_submit(&queued,&r)&&r&&live==1);
  if(mode==1)wr_iot_result_cancel(r);
  if(!immediate){
   assert(wr_iot_queue_dispatch(&queued,&queued,mode==0?NULL:execute_test));
   wr_iot_queue_cleanup(&queued);
  }
  enum wr_iot_work_state state=wr_iot_result_read(r,&status);
  if(mode==0)assert(state==WR_IOT_WORK_DONE&&status==-1&&!operation_calls);
  if(mode==1)assert(state==WR_IOT_WORK_CANCELLED&&!operation_calls);
  if(mode==2||mode==4)assert(state==WR_IOT_WORK_DONE&&!status&&operation_calls==1);
  if(mode==3)assert(state==WR_IOT_WORK_UNCERTAIN&&status==-1&&operation_calls==1);
  assert(r->refs.refs==1);wr_iot_result_put(r);assert(!live);
 }
 puts("PASS queued result/producer/worker: refs, rejection, cancellation, no-operation failure, early completion and terminal immutability; primitives injected");
 return 0;
}
