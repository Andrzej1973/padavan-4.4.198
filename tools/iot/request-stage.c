#include <stdio.h>
#include <net/if.h>
#include "request-stage.h"
#include "request.h"
#include "service-guard.h"
#include "rc.h"
#include <string.h>

static const char *wr_iot_request_nvram(void *context,const char *key)
{
 (void)context;
 return nvram_safe_get(key);
}

static int wr_iot_request_clear(void)
{
 int failed=0;
 failed |= nvram_set_int_temp("wr_iot_profile_t",0)!=0;
 failed |= nvram_set_int_temp("wr_iot_network_t",0)!=0;
 failed |= nvram_set_int_temp("wr_iot_firewall_t",0)!=0;
 failed |= nvram_set_temp("wr_iot_ssid_t","")!=0;
 failed |= nvram_set_temp("wr_iot_psk_t","")!=0;
 failed |= nvram_set_temp("wr_iot_gateway_t","")!=0;
 failed |= nvram_set_temp("wr_iot_mask_t","")!=0;
 failed |= nvram_set_temp("wr_iot_start_t","")!=0;
 failed |= nvram_set_temp("wr_iot_end_t","")!=0;
 return !failed;
}

static int wr_iot_request_stage_locked(int router_mode,int radio_on,int radio_mode)
{
 struct wr_iot_request request;
 /* Existing bridges belong to the activation/recovery controller. Staging
  * must never clear the live service gates or adopt a foreign bridge. */
 if(if_nametoindex("br-iot"))return 0;
 if(!wr_iot_request_read(&request,wr_iot_request_nvram,NULL,router_mode,radio_on,
                         radio_mode,NULL,0))return 0;
 if(!wr_iot_request_clear())return 0;
 if(!request.enabled)return 1;
 /* Each destination is fixed-size and the request parser already bounded it. */
 if(nvram_set_temp("wr_iot_ssid_t",request.ssid)||
    nvram_set_temp("wr_iot_psk_t",request.password)||
    nvram_set_temp("wr_iot_gateway_t",request.gateway)||
    nvram_set_temp("wr_iot_mask_t",request.mask)||
    nvram_set_temp("wr_iot_start_t",request.first)||
    nvram_set_temp("wr_iot_end_t",request.last)){
  (void)wr_iot_request_clear();return 0;
 }
 /* Profile generation may now add ra2. Network/firewall stay quarantined until
  * the activation backend has proven bridge, dnsmasq and firewall readiness. */
 if(nvram_set_int_temp("wr_iot_profile_t",1)){
  (void)wr_iot_request_clear();return 0;
 }
 return 1;
}

int wr_iot_request_stage(int router_mode,int radio_on,int radio_mode)
{
 int token=wr_iot_service_guard_enter(1),result;
 if(token!=1)return 0;
 result=wr_iot_request_stage_locked(router_mode,radio_on,radio_mode);
 wr_iot_service_guard_leave(token);
 return result;
}
