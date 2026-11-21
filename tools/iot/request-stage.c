#include <stdio.h>
#include <unistd.h>
#include <net/if.h>
#include "request-stage.h"
#include "request.h"
#include "network-check.h"
#include "bridge.h"
#include "service-guard.h"
#include "rc.h"
#include <string.h>

static const char *wr_iot_request_nvram(void *context,const char *key)
{
 static const struct {const char *field,*candidate;} fields[]={
  {"wr_iot_enable","wr_iot_request_enable"},
  {"wr_iot_ssid","wr_iot_request_ssid"},
  {"wr_iot_psk","wr_iot_request_psk"},
  {"wr_iot_gateway","wr_iot_request_gateway"},
  {"wr_iot_mask","wr_iot_request_mask"},
  {"wr_iot_start","wr_iot_request_start"},
  {"wr_iot_end","wr_iot_request_end"}
 };
 size_t i;
 (void)context;
 /* The authenticated form must write only candidate fields. Reading the
  * active profile here would let apply.cgi change it before activation. */
 for(i=0;i<sizeof(fields)/sizeof(fields[0]);i++)
  if(!strcmp(key,fields[i].field))return nvram_safe_get(fields[i].candidate);
 return NULL;
}

static int wr_iot_request_clear(void)
{
 static const char *keys[]={"wr_iot_ssid_t","wr_iot_psk_t","wr_iot_gateway_t",
                           "wr_iot_mask_t","wr_iot_start_t","wr_iot_end_t"};
 size_t i;
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
 if(strcmp(nvram_safe_get("wr_iot_profile_t"),"0")||
    strcmp(nvram_safe_get("wr_iot_network_t"),"0")||
    strcmp(nvram_safe_get("wr_iot_firewall_t"),"0"))failed=1;
 for(i=0;i<sizeof(keys)/sizeof(keys[0]);i++)
  if(nvram_safe_get(keys[i])[0])failed=1;
 return !failed;
}

static int wr_iot_gate_closed(const char *key)
{
 const char *value=nvram_safe_get(key);
 return value&&(!*value||!strcmp(value,"0"));
}

static int wr_iot_request_stage_locked(const char *(*read)(void *,const char *),
 void *context,int router_mode,int radio_on,int radio_mode)
{
 struct wr_iot_request request;
 /* Existing bridges or open service gates belong to activation/recovery.
  * Refuse them before validation or writes; only the controller may quiesce. */
 if(if_nametoindex("br-iot"))return 0;
 if(!wr_iot_gate_closed("wr_iot_profile_t")||
    !wr_iot_gate_closed("wr_iot_network_t")||
    !wr_iot_gate_closed("wr_iot_firewall_t"))return 0;
 if(!wr_iot_request_read(&request,read,context,router_mode,radio_on,
                         radio_mode,NULL,0))return 0;
 /* Validate live interface and route overlaps before any writes.
  * Activation must repeat validation if routing changes afterwards. */
 if(request.enabled&&!wr_iot_network_check(request.gateway,request.mask,
                                          request.first,request.last))return 0;
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
 /* This gate records a staged request only. Cold generation reserves ra2
  * independently; never call the physical radio generator from this path.
  * A precreated activation backend must match the loaded credentials under
  * its request/lifetime ownership before opening ra2. Network/firewall stay
  * quarantined until bridge, dnsmasq and firewall readiness is proven. */
 if(strcmp(nvram_safe_get("wr_iot_ssid_t"),request.ssid)||
    strcmp(nvram_safe_get("wr_iot_psk_t"),request.password)||
    strcmp(nvram_safe_get("wr_iot_gateway_t"),request.gateway)||
    strcmp(nvram_safe_get("wr_iot_mask_t"),request.mask)||
    strcmp(nvram_safe_get("wr_iot_start_t"),request.first)||
    strcmp(nvram_safe_get("wr_iot_end_t"),request.last)||
    nvram_set_int_temp("wr_iot_profile_t",1)||
    strcmp(nvram_safe_get("wr_iot_profile_t"),"1")){
  (void)wr_iot_request_clear();return 0;
 }
 return 1;
}

int wr_iot_request_stage_from(const char *(*read)(void *,const char *),void *context,
 int router_mode,int radio_on,int radio_mode)
{
 int token,result;
 if(!read)return 0;
 token=wr_iot_service_guard_enter(1);
 if(token!=1)return 0;
 result=wr_iot_request_stage_locked(read,context,router_mode,radio_on,radio_mode);
 wr_iot_service_guard_leave(token);
 return result;
}

int wr_iot_request_stage(int router_mode,int radio_on,int radio_mode)
{
 return wr_iot_request_stage_from(wr_iot_request_nvram,NULL,router_mode,radio_on,radio_mode);
}

static int wr_iot_request_stage_matches_gates(const struct wr_iot_request *request,
 const char *network,const char *firewall)
{
 static const char *const keys[]={"wr_iot_ssid_t","wr_iot_psk_t",
  "wr_iot_gateway_t","wr_iot_mask_t","wr_iot_start_t","wr_iot_end_t"};
 const char *expected[6];size_t capacities[6],i;int guard;
 if(!request||request->enabled!=1)return 0;
 guard=wr_iot_service_guard_dup();if(guard<0)return 0;
 if(close(guard))return 0;
#define FIELD(n,name) expected[n]=request->name;capacities[n]=sizeof(request->name)
 FIELD(0,ssid);FIELD(1,password);FIELD(2,gateway);FIELD(3,mask);FIELD(4,first);FIELD(5,last);
#undef FIELD
 if(strcmp(nvram_safe_get("wr_iot_profile_t"),"1")||
    strcmp(nvram_safe_get("wr_iot_network_t"),network)||
    strcmp(nvram_safe_get("wr_iot_firewall_t"),firewall))return 0;
 for(i=0;i<6;i++)if(!memchr(expected[i],0,capacities[i])||
    strcmp(nvram_safe_get(keys[i]),expected[i]))return 0;
 return 1;
}

int wr_iot_request_stage_matches(const struct wr_iot_request *request)
{
 return wr_iot_request_stage_matches_gates(request,"1","1");
}
int wr_iot_request_network_enable(const struct wr_iot_request *request)
{
 if(!wr_iot_request_stage_matches_gates(request,"0","0")||
    !wr_iot_bridge_is_owned()||!wr_iot_bss_is_down()||
    !wr_iot_bridge_address_matches(request->gateway,request->mask)||
    !wr_iot_network_check(request->gateway,request->mask,request->first,request->last)||
    !wr_iot_request_stage_matches_gates(request,"0","0"))return 0;
 /* A failing setter may still mutate. Retain outer snapshot/recovery and
  * never roll it back here or open the firewall/radio as compensation. */
 if(nvram_set_int_temp("wr_iot_network_t",1))return 0;
 return wr_iot_request_stage_matches_gates(request,"1","0")&&
    wr_iot_bridge_is_owned()&&wr_iot_bss_is_down()&&
    wr_iot_bridge_address_matches(request->gateway,request->mask);
}

int wr_iot_request_prepared_matches(const struct wr_iot_request *request,int network,int firewall)
{
 if((network!=0&&network!=1)||(firewall!=0&&firewall!=1))return 0;
 return wr_iot_request_stage_matches_gates(request,network?"1":"0",firewall?"1":"0");
}
