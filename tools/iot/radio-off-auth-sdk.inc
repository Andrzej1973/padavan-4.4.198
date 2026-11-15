static int wr_iot_off_auth_policy(const struct wr_iot_radio_off_policy *p)
{
 int stored,auth;
 if(!p||(p->stored_radio!=0&&p->stored_radio!=1)||
    (p->auth_required!=0&&p->auth_required!=1)||(!p->stored_radio&&p->auth_required))return 0;
 stored=get_enabled_radio_rt();
 auth=stored?!!is_need_8021x(nvram_wlan_get(0,"auth_mode")):0;
 return !get_ap_mode()&&get_mode_radio_rt()==0&&stored==p->stored_radio&&auth==p->auth_required;
}
enum wr_iot_off_auth_result wr_iot_rc_radio_off_auth(
 const struct wr_iot_radio_off_policy *p,const struct wr_iot_physical_stop_request *r)
{
 int fd,result=0;
 fd=wr_iot_service_guard_dup();if(fd<0)return WR_OFF_AUTH_REFUSED;
 if(close(fd)||!wr_iot_off_auth_policy(p)||!wr_iot_radio_off_observed(r))return WR_OFF_AUTH_REFUSED;
 /* Stock start_8021x_rt can launch enterprise auth before find_wlan_if_up.
  * No2GHz UP interface is allowed here; borrowed name is never retained. */
 if(find_wlan_if_up(0))return WR_OFF_AUTH_REFUSED;
 if(p->auth_required){
  if(!wr_iot_off_auth_policy(p)||!wr_iot_radio_off_observed(r))return WR_OFF_AUTH_REFUSED;
  result=eval("rtinicapd","-i",IFNAME_2G_MAIN);
 }
 if(result||!wr_iot_off_auth_policy(p)||find_wlan_if_up(0)||!wr_iot_radio_off_observed(r))return WR_OFF_AUTH_UNCERTAIN;
 fd=wr_iot_service_guard_dup();if(fd<0)return WR_OFF_AUTH_UNCERTAIN;
 return close(fd)?WR_OFF_AUTH_UNCERTAIN:WR_OFF_AUTH_RETURNED;
}
