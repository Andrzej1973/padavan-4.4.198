#ifndef WR_IOT_RESTART_WAN_PLAN_H
#define WR_IOT_RESTART_WAN_PLAN_H
enum wr_iot_wan_followup {WR_WAN_INVALID=-1,WR_WAN_NONE,WR_WAN_FULL_RESTART,WR_WAN_RECONNECT};
/* Exact SDK check_apcli_wan decision, with identities already resolved by its
 * interface helpers: -1 neither APCLI,0 2GHz,1 5GHz. Pure planning only.
 * Run follow-up after the radio transaction has released its ownership;
 * this plan alone never authorizes WAN mutation or provides readiness proof. */
static inline enum wr_iot_wan_followup wr_iot_restart_wan_plan(
 int ap_mode,int man_band,int wisp_band,int changed_band,int radio_on)
{
 if((ap_mode!=0&&ap_mode!=1)||man_band< -1||man_band>1||wisp_band< -1||wisp_band>1||
    (changed_band!=0&&changed_band!=1)||(radio_on!=0&&radio_on!=1))return WR_WAN_INVALID;
 if(ap_mode)return WR_WAN_NONE;
 if(man_band!=wisp_band)return WR_WAN_FULL_RESTART;
 if(radio_on&&wisp_band==changed_band)return WR_WAN_RECONNECT;
 return WR_WAN_NONE;
}
#endif
