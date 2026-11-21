static PRTMP_ADAPTER current_ad;
static int mode,operation_calls;
static int operation(PRTMP_ADAPTER ad){
 struct wr_iot_queue_envelope *e;
 assert(ad==current_ad&&!held&&owned);operation_calls++;
 e=owned->buffer;
 if(mode==7)wr_iot_result_cancel(e->result);
 return 0;
}
static void consume(void){
 PCmdQElmt cmd=owned;assert(cmd&&!held);
 /* Mode 8 models HALT skip: same unconditional cleanup follows. */
 if(mode!=8)assert(wr_iot_queue_dispatch(current_ad,cmd,mode==5?NULL:operation));
 wr_iot_queue_cleanup(cmd);
 os_free_mem(current_ad,cmd->buffer);os_free_mem(current_ad,cmd);owned=NULL;
}
static void composition_wake(int *task){
 assert(task==&current_ad->cmdQTask&&!held);wakes++;
 if(mode==9)consume(); /* Worker completes before enqueue returns. */
}
int main(void){
 struct adapter ad;struct wr_iot_queued_result *r;int ret,status;
 for(mode=0;mode<=10;mode++){
  memset(&ad,0,sizeof(ad));current_ad=&ad;ad.CmdQ.CmdQState=mode==3?0:1;
  ad.flags=mode==0?1:0;allocations=frees=held=queued=wakes=operation_calls=0;
  fail_at=mode==1?1:mode==2?2:0;fail_alloc=mode==4;owned=NULL;assert(!live);
  ret=wr_iot_queue_submit(&ad,&r);
  if(mode<=4){
   assert(ret==(mode==0||mode==3?1:2)&&!r&&!owned&&!live&&!wakes);
   assert(frees==(mode==2?1:mode==3?2:0));continue;
  }
  assert(!ret&&r&&live==1&&queued==1&&wakes==1);
  if(mode==6)wr_iot_result_cancel(r);
  if(mode==10){
   /* Caller exits first; queue ref still owns result through worker cleanup. */
   wr_iot_result_cancel(r);wr_iot_result_put(r);assert(live==1);
   consume();assert(!live&&!owned&&frees==2&&!operation_calls);continue;
  }
  if(mode!=9)consume();
  enum wr_iot_work_state state=wr_iot_result_read(r,&status);
  if(mode==5)assert(state==WR_IOT_WORK_DONE&&status==-1&&!operation_calls);
  if(mode==6||mode==8)assert(state==WR_IOT_WORK_CANCELLED&&!operation_calls);
  if(mode==7)assert(state==WR_IOT_WORK_UNCERTAIN&&status==-1&&operation_calls==1);
  if(mode==9)assert(state==WR_IOT_WORK_DONE&&!status&&operation_calls==1);
  assert(!owned&&frees==2&&r->refs.refs==1);wr_iot_result_put(r);assert(!live);
 }
 puts("PASS actual enqueue plus producer/worker: reject/allocation, timeout/HALT cleanup, running uncertainty, early worker completion; OS primitives injected");
 return 0;
}
