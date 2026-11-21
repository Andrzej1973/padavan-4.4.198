int wr_iot_rc_radio_off_state(const struct wr_iot_radio_off_policy *policy,
 const struct wr_iot_physical_stop_request *released)
{
 int fd;
 if(!policy||(policy->reload!=0&&policy->reload!=1)||
    (policy->stored_radio!=0&&policy->stored_radio!=1))return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(get_ap_mode()||get_mode_radio_rt()!=0||get_enabled_radio_rt()!=policy->stored_radio||
    !wr_iot_radio_off_observed(released))return 0;
 if(policy->reload)nvram_set_int_temp("reload_svc_rt",1);
 /* Same RAM key as SDK start_wifi_ap_rt(0), without its combined lifecycle. */
 mlme_state_rt(0);
 if(nvram_get_int("mlme_radio_rt")!=0||get_ap_mode()||get_mode_radio_rt()!=0||
    get_enabled_radio_rt()!=policy->stored_radio||!wr_iot_radio_off_observed(released))return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 return 1;
}
