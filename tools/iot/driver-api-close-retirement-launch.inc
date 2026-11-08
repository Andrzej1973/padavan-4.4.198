/* Staged orchestration; caller pins registration/adapter and holds RTNL.
 * handle is caller-owned storage that MUST survive any error with *handle!=NULL.
 * Never discard/retry/overwrite an ambiguous task handle. This helper does not
 * install an ioctl, retire OPEN/isolation fences or acquire firmware authority. */
static INT wr_iot_driver_close_retirement_launch(RTMP_ADAPTER *ad,
 struct task_struct **handle)
{
 int status,canceled;
 if(!ad||!handle||*handle)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 status=wr_iot_driver_close_retirement_prepare_fixed(ad,handle);
 if(status)return status;
 status=wr_iot_driver_close_retirement_start(ad,handle);
 if(!status)return 0;
 /* Cancel itself rejects started/entered tasks before kthread_stop. Only a
  * proven never-woken task may be stopped while this caller holds RTNL. */
 canceled=wr_iot_driver_close_retirement_cancel(ad,handle);
 return canceled?-EUCLEAN:status;
}
