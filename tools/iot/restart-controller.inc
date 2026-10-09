/* Installed into services_ex.c, after the raw start/stop definitions.
 * Verify configured DNS and DHCPv4 handlers before commit and after recovery. */
#if defined(BOARD_WR1200JS)
#include "dns-ready.h"
#include "dns-config.h"
#include "dhcp-ready.h"
#include "dns-sockets.h"
#ifndef WR_IOT_DNS_CONFIG_PATH
#define WR_IOT_DNS_CONFIG_PATH "/etc/dnsmasq.conf"
#endif
#ifndef WR_IOT_DNS_PROBE
#define WR_IOT_DNS_PROBE wr_iot_dns_handler_ready
#endif
#ifndef WR_IOT_DNS_LAN_PROBE
#define WR_IOT_DNS_LAN_PROBE wr_iot_dns_handler_ready_at
#endif
#ifndef WR_IOT_DHCP_PROBE
#define WR_IOT_DHCP_PROBE(address) wr_iot_dhcp_ready_at(address,67)
#endif
#ifndef WR_IOT_DHCP_GATEWAY
#define WR_IOT_DHCP_GATEWAY wr_iot_dhcp_gateway
#endif
#ifndef WR_IOT_SOCKET_READY
static int wr_iot_restart_socket_ready(unsigned int port,int dhcp4)
{
 struct wr_iot_dns_sockets sockets;
 return wr_iot_dns_selected_sockets("/usr/sbin/dnsmasq",&sockets)&&sockets.dns_port==port&&(!dhcp4||sockets.dhcp_standard);
}
#define WR_IOT_SOCKET_READY wr_iot_restart_socket_ready
#endif
#ifndef WR_IOT_SERVICE_LOCK_PATH
#define WR_IOT_SERVICE_LOCK_PATH "/var/run/wr-iot-services.lock"
#endif
static struct wr_iot_service_state wr_iot_restart_state;
static int wr_iot_restart_active,wr_iot_restart_guard,wr_iot_restart_bound;
static int wr_iot_restart_old_running,wr_iot_restart_stopped_candidate;
static unsigned int wr_iot_restart_old_port;
static int wr_iot_restart_old_dhcp4;
static char wr_iot_restart_old_gateway[16];
#ifndef WR_IOT_LEASE_PATH
#define WR_IOT_LEASE_PATH "/tmp/dnsmasq.leases"
#endif
static struct wr_iot_saved_file wr_iot_restart_lease;
static struct wr_iot_generated_file wr_iot_restart_lease_generated;
static int wr_iot_restart_lease_captured,wr_iot_restart_lease_owned;
static int wr_iot_restart_lease_observed,wr_iot_restart_lease_restored;
static int wr_iot_restart_wait(int running)
{
 int i;
 for(i=0;i<20;i++){
  if(!!is_dns_dhcpd_run()==!!running)return 1;
  usleep(50000);
 }
 return 0;
}
static int wr_iot_restart_service_wait(unsigned int port,int dhcp4,const char *gateway)
{
 int i;
 for(i=0;i<20;i++){
  if(is_dns_dhcpd_run()&&WR_IOT_SOCKET_READY(port,dhcp4)&&(!port||WR_IOT_DNS_PROBE(port)||(gateway[0]&&WR_IOT_DNS_LAN_PROBE(gateway,port)))&&(!dhcp4||WR_IOT_DHCP_PROBE(gateway)))return 1;
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
 wr_iot_saved_release(&wr_iot_restart_lease);
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
 if(wr_iot_restart_lease_captured&&wr_iot_restart_lease_owned&&!wr_iot_restart_lease_restored){
  /* Only observe the candidate daemon's lease output after it is stopped.
   * Retain that identity on retry rather than adopting a later foreign write. */
  if(!wr_iot_restart_lease_observed){
   if(!wr_iot_generated_capture(&wr_iot_restart_lease_generated,WR_IOT_LEASE_PATH))return 0;
   wr_iot_restart_lease_observed=1;
  }
  if(!wr_iot_saved_restore(&wr_iot_restart_lease,&wr_iot_restart_lease_generated,WR_IOT_LEASE_PATH))return 0;
  wr_iot_restart_lease_restored=1;
 }
 if(wr_iot_restart_old_running){
  /* Start from restored files, without generating another configuration. */
  if(!is_dns_dhcpd_run()&&eval("/usr/sbin/dnsmasq"))return 0;
  if(!wr_iot_restart_service_wait(wr_iot_restart_old_port,wr_iot_restart_old_dhcp4,wr_iot_restart_old_gateway))return 0;
 }else if(!wr_iot_restart_wait(0))return 0;
 return wr_iot_restart_finish();
}
static int wr_iot_restart_transaction(void)
{
 int result,new_dhcp4;unsigned int new_port;char new_gateway[16]={0};
 if(wr_iot_restart_active){
  if(!wr_iot_restart_recover())return EBUSY;
  /* Recovery retry does not immediately attempt another new configuration. */
  return EAGAIN;
 }
 wr_iot_restart_old_running=!!is_dns_dhcpd_run();wr_iot_restart_old_port=0;wr_iot_restart_old_dhcp4=0;wr_iot_restart_old_gateway[0]=0;
 if(wr_iot_restart_old_running&&!wr_iot_dns_config_services(WR_IOT_DNS_CONFIG_PATH,&wr_iot_restart_old_port,&wr_iot_restart_old_dhcp4))return EINVAL;
 if((wr_iot_restart_old_port||wr_iot_restart_old_dhcp4)&&!WR_IOT_DHCP_GATEWAY(IFNAME_BR,wr_iot_restart_old_gateway)&&wr_iot_restart_old_dhcp4)return EINVAL;
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
 wr_iot_restart_lease_captured=0;wr_iot_restart_lease_owned=0;
 wr_iot_restart_lease_observed=0;wr_iot_restart_lease_restored=0;
 memset(&wr_iot_restart_lease,0,sizeof(wr_iot_restart_lease));
 wr_iot_restart_active=1;wr_iot_restart_bound=1;
 wr_iot_restart_stopped_candidate=0;
 wr_iot_stop_dns_raw();
 result=wr_iot_restart_wait(0)?0:EBUSY;
 if(!result&&!wr_iot_writer_journal_failed()){
  /* Capture after old daemon exit so its final lease flush is included. */
  if(!wr_iot_saved_capture(&wr_iot_restart_lease,WR_IOT_LEASE_PATH))result=EIO;
  else {
   wr_iot_restart_lease_captured=1;wr_iot_restart_lease_owned=1;
   result=wr_iot_start_dns_raw(get_ap_mode());
  }
 }
 else if(!result)result=EIO;
 if(!result&&(wr_iot_writer_journal_failed()||!wr_iot_dns_config_services(WR_IOT_DNS_CONFIG_PATH,&new_port,&new_dhcp4)||
    ((new_port||new_dhcp4)&&!WR_IOT_DHCP_GATEWAY(IFNAME_BR,new_gateway)&&new_dhcp4)||
    !wr_iot_restart_service_wait(new_port,new_dhcp4,new_gateway)||
    !wr_iot_service_state_seal(&wr_iot_restart_state,WR_IOT_SERVICE_LOCK_PATH)))result=EIO;
 if(!result&&wr_iot_restart_finish())return 0;
 if(!result)result=EIO;
 if(!wr_iot_restart_recover())
  logmessage("IoT Wi-Fi","DNS/DHCP recovery incomplete; snapshots and service lock retained");
 return result;
}
#endif
