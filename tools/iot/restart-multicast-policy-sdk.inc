int wr_iot_rc_restart_multicast_policy(struct wr_iot_multicast_policy *out)
{
 struct wr_iot_multicast_policy p={0};int fd,raw=0,again=0;
 if(!out)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(get_ap_mode()||get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1)return 0;
 if(!wr_iot_rc_restart_guest_policy(&p.guest))return 0;
#if !defined(USE_IGMP_SNOOP)
 p.required=1;raw=nvram_wlan_get_int(0,"IgmpSnEnable");p.enabled=!!raw;
#endif
 if(get_ap_mode()||get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1)return 0;
#if !defined(USE_IGMP_SNOOP)
 again=nvram_wlan_get_int(0,"IgmpSnEnable");if(raw!=again)return 0;
#else
 (void)raw;(void)again;
#endif
 {int guest;if(!wr_iot_rc_restart_guest_policy(&guest)||guest!=p.guest)return 0;}
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 *out=p;return 1;
}
