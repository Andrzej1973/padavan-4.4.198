/* Synchronous RTNL owner only. Move the old cache, never copy its PID ownership.
 * Restore it on failed admission; put its PID only after the new ARM succeeds.
 * No endpoint. Include after ARM admission and terminal helpers. */
static INT __attribute__((unused)) wr_iot_physical_stop_arm_replace_terminal(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_stop_request *request,unsigned long *serial)
{
 struct wr_iot_physical_stop_terminal old={0},empty={0};ULONG flags=0;
 int moved=0,status;
 if(!ad||!main_dev||!serial||!wr_iot_physical_stop_request_valid(request)||
    request->action!=WR_STOP_ARM)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 if(!ad->wr_iot_physical_terminal.owner){
  status=ad->wr_iot_physical_terminal.ready||ad->wr_iot_physical_terminal.status?
    -EUCLEAN:0;
 }else{
  struct wr_iot_physical_stop_terminal *cached=&ad->wr_iot_physical_terminal;
  status=-EBUSY;
  if(cached->ready&&cached->owner==task_pid(current)&&
     ((cached->status==WR_STOP_CANCELLED&&cached->request.action==WR_STOP_CANCEL)||
      (cached->status==WR_STOP_RELEASED&&cached->request.action==WR_STOP_RELEASE))&&
     !wr_iot_physical_stop_nonce_equal(cached->request.nonce,request->nonce)&&
     !wr_iot_physical_stop_blocks_retirement(&ad->wr_iot_physical_stop,
       &ad->wr_iot_physical_pins)&&
     !ad->wr_iot_physical_pending_pins.module&&!ad->wr_iot_physical_pending_pins.task&&
     !ad->wr_iot_physical_pending_pins.device){
   old=*cached;*cached=empty;moved=1;status=0;
  }
 }
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(status)return status;
 status=wr_iot_physical_stop_arm_admit(ad,main_dev,request,serial);
 if(!moved)return status;
 if(status){
  /* RTNL excludes another cache writer throughout this synchronous operation.
   * Admission failure published neither record nor reference ownership. */
  RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
  ad->wr_iot_physical_terminal=old;old=empty;
  RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
  return status;
 }
 wr_iot_physical_stop_terminal_clear(&old); /* actual PID put outside locks */
 return 0;
}
