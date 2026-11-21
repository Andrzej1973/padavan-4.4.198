/* Caller pins adapter/registration throughout admission (normally RTNL).
 * -1: ownership rejected; 0: owner and caller scheduled;
 * 1: ownership accepted but retained/pending scheduling recovery.
 * Neither nonnegative result permits releasing the original open/module pin.
 * Ticket is the original incomplete-close receipt; NULL means acquired open.
 * This entry is staged; ordinary ndo callbacks remain unbound. */
INT wr_iot_mbss_recovery_handoff(RTMP_ADAPTER *ad,PNET_DEV dev,
 unsigned long generation,const struct wr_iot_radio_ticket *ticket)
{
 int owner,caller;
 if(ticket)owner=wr_iot_mbss_recovery_submit_close(ad,dev,generation,ticket);
 else owner=wr_iot_mbss_recovery_submit(ad,dev,generation);
 if(owner<0)return -1;
 caller=wr_iot_mbss_poll_schedule(ad);
 return owner==0&&caller==0?0:1;
}
