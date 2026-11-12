/* Fixed retirement body for the isolated candidate. API active fence remains:
 * lifetime-reference retirement is not RF/FIFO/late-TxS or reopen proof.
 * Candidate progress can launch this body after checked ownership readiness.
 * Linux 4.4 direct do_exit completes kthread_stop via exit_mm/mm_release;
 * completion is not task deallocation. Do not kthread_stop a started instance
 * while holding RTNL: this body acquires RTNL itself. Only never-woken task
 * cancellation is supported by the staged cancel helper. */
static int wr_iot_driver_close_retirement_thread(void *context)
{
 RTMP_ADAPTER *ad=context;int status;
 rtnl_lock();
 status=wr_iot_driver_close_retirement_thread_enter(ad);
 if(!status&&!wr_iot_driver_close_retirement_thread_claim(ad))status=-EBUSY;
 if(status){
  (void)wr_iot_driver_close_retirement_thread_refuse(ad,status);
  rtnl_unlock();
  return status; /* API still holds its module reference. */
 }
 /* Local task now owns the module reference. No adapter access past claim. */
 rtnl_unlock();
 module_put_and_exit(0);
}
static INT wr_iot_driver_close_retirement_prepare_fixed(RTMP_ADAPTER *ad,
 struct task_struct **out)
{
 return wr_iot_driver_close_retirement_prepare(ad,
  wr_iot_driver_close_retirement_thread,out);
}
