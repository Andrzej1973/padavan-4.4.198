int wr_iot_rc_radio_on_rollback_state(const struct wr_iot_physical_stop_request *released)
{
 int fd;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(get_ap_mode()||get_mode_radio_rt()!=0||
    !wr_iot_radio_recovery_down_observed(released))return 0;
 /* Restoring OFF does not alter saved radio_x or the consumable reload event. */
 mlme_state_rt(0);
 if(nvram_get_int("mlme_radio_rt")!=0||get_ap_mode()||get_mode_radio_rt()!=0||
    !wr_iot_radio_recovery_down_observed(released))return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 return 1;
}
