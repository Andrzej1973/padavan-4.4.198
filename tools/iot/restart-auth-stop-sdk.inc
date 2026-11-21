/* Included only by prepared WR1200JS net_wifi.c. Fixed SDK process-name
 * semantics; this does not establish PID ownership or data-path completion. */
int wr_iot_auth_stop_present(void)
{
 int fd,result;
 fd=wr_iot_service_guard_dup();if(fd<0)return -1;if(close(fd))return -1;
 if(get_ap_mode()||get_mode_radio_rt()!=0)return -1;
 result=pids("rtinicapd");
 if(get_ap_mode()||get_mode_radio_rt()!=0)return -1;
 return result<0?-1:!!result;
}
int wr_iot_auth_stop_signal(int sig)
{
 int present;
 if(sig!=SIGTERM&&sig!=SIGKILL)return 0;
 present=wr_iot_auth_stop_present();if(present<0)return 0;if(!present)return 1;
 /* Same fixed service and signal arguments as SDK kill_services, without
  * its sleeps or forced escalation loop. Controller owns both attempts. */
 return doSystem("killall %s %s",sig==SIGTERM?"-q":"-SIGKILL","rtinicapd")==0;
}
