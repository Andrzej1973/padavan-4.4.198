/* Administrative indication only, never readiness or RF/DMA evidence. */
int wr_iot_rc_restart_led_on(void)
{
 int token;
 token=wr_iot_service_guard_enter(1);if(token!=1)return 0;
 if(get_ap_mode()||get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1||
    !is_interface_up(IFNAME_2G_MAIN)){
  wr_iot_service_guard_leave(token);return 0;
 }
 /* Exact stock helper is a compile-time no-op for USE_WID_2G7603. */
 /* No VgaClamp command exists in the7603 branch of that helper. */
 LED_CONTROL(LED_SW2G,LED_ON);
 wr_iot_service_guard_leave(token);return 1;
}
