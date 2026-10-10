#include "request-stage.h"
#include "request.h"
#include "rc.h"
#include <string.h>

static const char *wr_iot_request_nvram(void *context,const char *key)
{
 (void)context;
 return nvram_safe_get(key);
}

static void wr_iot_request_clear(void)
{
 nvram_set_int_temp("wr_iot_profile_t",0);
 nvram_set_int_temp("wr_iot_network_t",0);
 nvram_set_int_temp("wr_iot_firewall_t",0);
 nvram_set_temp("wr_iot_gateway_t","");
 nvram_set_temp("wr_iot_mask_t","");
 nvram_set_temp("wr_iot_start_t","");
 nvram_set_temp("wr_iot_end_t","");
}

int wr_iot_request_stage(int router_mode,int radio_on,int radio_mode)
{
 struct wr_iot_request request;
 if(!wr_iot_request_read(&request,wr_iot_request_nvram,NULL,router_mode,radio_on,
                         radio_mode,NULL,0))return 0;
 wr_iot_request_clear();
 if(!request.enabled)return 1;
 /* Each destination is fixed-size and the request parser already bounded it. */
 nvram_set_temp("wr_iot_gateway_t",request.gateway);
 nvram_set_temp("wr_iot_mask_t",request.mask);
 nvram_set_temp("wr_iot_start_t",request.first);
 nvram_set_temp("wr_iot_end_t",request.last);
 /* Profile generation may now add ra2. Network/firewall stay quarantined until
  * the activation backend has proven bridge, dnsmasq and firewall readiness. */
 nvram_set_int_temp("wr_iot_profile_t",1);
 return 1;
}
