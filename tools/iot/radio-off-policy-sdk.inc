/* Embed beside existing SDK helpers only after the policy header. Caller owns
 * active admission/service guard. Repeated reads detect observed drift; they
 * do not assert atomicity against writers outside the service guard. */
int wr_iot_rc_radio_off_policy(int reload,struct wr_iot_radio_off_policy *out)
{
 struct wr_iot_radio_off_policy a={0},b={0};int fd;
 if(!out||(reload!=0&&reload!=1)||!wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(get_ap_mode()||get_mode_radio_rt()!=0)return 0;
 a.reload=b.reload=reload;
 a.stored_radio=get_enabled_radio_rt();
 if(a.stored_radio!=0&&a.stored_radio!=1)return 0;
 a.auth_required=a.stored_radio?!!is_need_8021x(nvram_wlan_get(0,"auth_mode")):0;
 if(!wr_iot_rc_restart_wan_plan(0,&a.wan))return 0;
 b.stored_radio=get_enabled_radio_rt();
 if(b.stored_radio!=0&&b.stored_radio!=1)return 0;
 b.auth_required=b.stored_radio?!!is_need_8021x(nvram_wlan_get(0,"auth_mode")):0;
 if(!wr_iot_rc_restart_wan_plan(0,&b.wan)||
    a.stored_radio!=b.stored_radio||a.auth_required!=b.auth_required||a.wan!=b.wan||
    a.wan<WR_WAN_NONE||a.wan>WR_WAN_FULL_RESTART||get_ap_mode()||get_mode_radio_rt()!=0||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 *out=a;return 1;
}
