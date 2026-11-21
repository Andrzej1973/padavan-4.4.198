int wr_iot_rc_restart_radio_state(int reload)
{
 int fd;
 if(reload!=0&&reload!=1)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(get_ap_mode()||get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1||
    !wr_iot_restart_main_down())return 0;
 if(reload){
  nvram_set_int_temp("reload_svc_rt",1);
  /* Watchdog consumes this event by clearing it; readback is not a receipt. */
 }
 /* Stock mlme_state_rt writes this exact RAM NVRAM key, not an RF register. */
 mlme_state_rt(1);
 if(nvram_get_int("mlme_radio_rt")!=1||get_ap_mode()||
    get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1||!wr_iot_restart_main_down())return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 return 1;
}
