/* Installed into services_ex.c, after the raw start/stop definitions.
 * Process presence is a provisional readiness check; DNS/DHCP probes are pending. */
#if defined(BOARD_WR1200JS)
#ifndef WR_IOT_SERVICE_LOCK_PATH
#define WR_IOT_SERVICE_LOCK_PATH "/var/run/wr-iot-services.lock"
#endif
static struct wr_iot_service_state wr_iot_restart_state;
static int wr_iot_restart_active,wr_iot_restart_guard,wr_iot_restart_bound;
static int wr_iot_restart_old_running,wr_iot_restart_stopped_candidate;
static int wr_iot_restart_wait(int running)
{
 int i;
 for(i=0;i<20;i++){
  if(!!is_dns_dhcpd_run()==!!running)return 1;
  usleep(50000);
 }
 return 0;
}
static int wr_iot_restart_finish(void)
{
 if(wr_iot_restart_bound){
  if(!wr_iot_writer_journal_unbind(&wr_iot_restart_state.transaction))return 0;
  wr_iot_restart_bound=0;
 }
 if(!wr_iot_service_state_finish(&wr_iot_restart_state,WR_IOT_SERVICE_LOCK_PATH))return 0;
 wr_iot_restart_active=0;
 wr_iot_service_guard_leave(wr_iot_restart_guard);wr_iot_restart_guard=0;
 return 1;
}
static int wr_iot_restart_recover(void)
{
 if(!wr_iot_restart_stopped_candidate){
  wr_iot_stop_dns_raw();
  if(!wr_iot_restart_wait(0))return 0;
  wr_iot_restart_stopped_candidate=1;
 }
 if(!wr_iot_service_state_recover(&wr_iot_restart_state,WR_IOT_SERVICE_LOCK_PATH))return 0;
 if(wr_iot_restart_old_running){
  /* Start from restored files, without generating another configuration. */
  if(!is_dns_dhcpd_run()&&eval("/usr/sbin/dnsmasq"))return 0;
  if(!wr_iot_restart_wait(1))return 0;
 }else if(!wr_iot_restart_wait(0))return 0;
 return wr_iot_restart_finish();
}
static int wr_iot_restart_transaction(void)
{
 int result;
 if(wr_iot_restart_active){
  if(!wr_iot_restart_recover())return EBUSY;
  /* Recovery retry does not immediately attempt another new configuration. */
  return EAGAIN;
 }
 wr_iot_restart_guard=wr_iot_service_guard_enter(1);
 if(wr_iot_restart_guard!=1)return EBUSY;
 wr_iot_service_state_init(&wr_iot_restart_state);
 if(!wr_iot_service_state_begin_guarded(&wr_iot_restart_state,WR_IOT_SERVICE_LOCK_PATH,IFNAME_BR)){
  wr_iot_service_guard_leave(wr_iot_restart_guard);wr_iot_restart_guard=0;return EIO;
 }
 if(!wr_iot_service_state_track(&wr_iot_restart_state,WR_IOT_SERVICE_LOCK_PATH)||
    !wr_iot_writer_journal_bind_state(&wr_iot_restart_state)){
  /* No writers have run: release the failed snapshot directly. */
  wr_iot_bundle_release(&wr_iot_restart_state.transaction.files);
  wr_iot_service_lock_release(&wr_iot_restart_state.transaction.lock);
  wr_iot_restart_state.transaction.active=0;
  wr_iot_service_guard_leave(wr_iot_restart_guard);wr_iot_restart_guard=0;return EIO;
 }
 wr_iot_restart_active=1;wr_iot_restart_bound=1;
 wr_iot_restart_old_running=!!is_dns_dhcpd_run();wr_iot_restart_stopped_candidate=0;
 wr_iot_stop_dns_raw();
 result=wr_iot_restart_wait(0)?0:EBUSY;
 if(!result&&!wr_iot_writer_journal_failed())result=wr_iot_start_dns_raw(get_ap_mode());
 else if(!result)result=EIO;
 if(!result&&(wr_iot_writer_journal_failed()||!wr_iot_restart_wait(1)||
    !wr_iot_service_state_seal(&wr_iot_restart_state,WR_IOT_SERVICE_LOCK_PATH)))result=EIO;
 if(!result&&wr_iot_restart_finish())return 0;
 if(!result)result=EIO;
 if(!wr_iot_restart_recover())
  logmessage("IoT Wi-Fi","DNS/DHCP recovery incomplete; snapshots and service lock retained");
 return result;
}
#endif
