/* Source adapter only; never invokes restart/reconnect. */
static int wr_iot_wan_name(char out[16],const char *name,int optional)
{
 size_t n;
 memset(out,0,16);
 if(!name)return optional;
 n=strnlen(name,16);if(n>=16)return 0;
 memcpy(out,name,n);return 1;
}
static int wr_iot_wan_band(const char*name)
{
 if(!strcmp(name,IFNAME_2G_APCLI))return 0;
#if BOARD_HAS_5G_RADIO
 if(!strcmp(name,IFNAME_5G_APCLI))return 1;
#endif
 return -1;
}
int wr_iot_rc_restart_wan_plan(int radio_on,enum wr_iot_wan_followup*out)
{
 char man[16],wisp[16],again_man[16],again_wisp[16];int fd,ap;
 if(!out||(radio_on!=0&&radio_on!=1))return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 ap=!!get_ap_mode();
 if(ap){
  if(!get_ap_mode())return 0;
  fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
  *out=WR_WAN_NONE;return 1;
 }
 if(!wr_iot_wan_name(man,get_man_ifname(0),0)||
    !wr_iot_wan_name(wisp,get_apcli_wisp_ifname(),1)||
    !wr_iot_wan_name(again_man,get_man_ifname(0),0)||
    !wr_iot_wan_name(again_wisp,get_apcli_wisp_ifname(),1)||
    strcmp(man,again_man)||strcmp(wisp,again_wisp)||get_ap_mode())return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 *out=wr_iot_restart_wan_plan(0,wr_iot_wan_band(man),wr_iot_wan_band(wisp),0,radio_on);
 return *out!=WR_WAN_INVALID;
}

void wr_iot_rc_restart_wan_submit(enum wr_iot_wan_followup plan)
{
 /* Fixed SDK calls; caller records attempt and owns post-radio ordering. */
 if(plan==WR_WAN_FULL_RESTART)full_restart_wan();
 else if(plan==WR_WAN_RECONNECT)try_wan_reconnect(1,0);
}

int wr_iot_rc_restart_wan_current(int radio_on,enum wr_iot_wan_followup expected)
{
 enum wr_iot_wan_followup current;int token,valid;
 token=wr_iot_service_guard_enter(1);if(token!=1)return 0;
 valid=wr_iot_rc_restart_wan_plan(radio_on,&current)&&current==expected;
 wr_iot_service_guard_leave(token);return valid;
}
