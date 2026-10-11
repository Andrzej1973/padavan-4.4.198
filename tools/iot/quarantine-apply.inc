/* Installed after the actual firewall builder. No radio/bridge is opened. */
#if defined(BOARD_WR1200JS)
#include "wr-iot/quarantine.h"
int wr_iot_active_filter_ready(const char *lan,const char *wan)
{
#if defined(USE_IPV6)
 struct wr_iot_firewall rules;
 if (!nvram_match("wr_iot_network_t","1") ||
     !nvram_match("wr_iot_firewall_t","1") ||
     !wr_iot_active_filter_plan(&rules,lan,wan)) return 0;
 return wr_iot_policy_rules_ready(rules.ipv4,rules.ipv6);
#else
 return 0;
#endif
}
int wr_iot_quarantine_apply(void)
{
#if defined(USE_IPV6)
 if (!nvram_match("wr_iot_network_t","0") ||
     !nvram_match("wr_iot_firewall_t","0") ||
     !wr_iot_quarantine_can_apply()) return 0;
 /* Includes the configured post-firewall scripts. Validate their final rules,
  * since successful generation alone does not establish installed isolation. */
 start_firewall_ex();
 return nvram_match("wr_iot_network_t","0") &&
        nvram_match("wr_iot_firewall_t","0") && wr_iot_quarantine_ready();
#else
 return 0;
#endif
}
static int wr_iot_policy_current_wan(char out[16])
{
 const char *value=get_wan_unit_value(0,"ifname_t");
 size_t n=strlen(value);
 if(n>=16)return 0;
 memset(out,0,16);
 if(n)memcpy(out,value,n+1);
 else get_wan_ifname(out);
 return strnlen(out,16)<16 && wr_iot_fw_ifname(out) && strcmp(out,IFNAME_BR);
}
int wr_iot_active_filter_apply(const char *lan,const char *wan)
{
#if defined(USE_IPV6)
 struct wr_iot_firewall rules;
 if (!nvram_match("wr_iot_network_t","1") ||
     !nvram_match("wr_iot_firewall_t","1") ||
     !wr_iot_policy_can_apply() ||
     !wr_iot_active_filter_plan(&rules,lan,wan)) return 0;
 start_firewall_ex();
 /* Scripts may have changed configuration or installed rules. Recompute and
  * observe after every writer; keep BSS closed and recovery state on failure. */
 return wr_iot_active_filter_ready(lan,wan);
#else
 return 0;
#endif
}
int wr_iot_active_filter_apply_current(void)
{
 char before[16],after[16];
 if(!wr_iot_policy_current_wan(before) ||
    !wr_iot_active_filter_apply(IFNAME_BR,before))return 0;
 return wr_iot_policy_current_wan(after) && !strcmp(before,after) &&
        wr_iot_active_filter_ready(IFNAME_BR,after);
}
int wr_iot_policy_enable_current(void)
{
 char gateway[16];const char *value;size_t n;
 if(!nvram_match("wr_iot_network_t","1") ||
    !nvram_match("wr_iot_firewall_t","0") ||
    !wr_iot_policy_can_apply())return 0;
 value=nvram_safe_get("wr_iot_gateway_t");n=strlen(value);
 if(n>=sizeof(gateway))return 0;
 memcpy(gateway,value,n+1);
 if(!wr_iot_network_services_ready(gateway))return 0;
 if(!nvram_set_int_temp("wr_iot_firewall_t",1) &&
    nvram_match("wr_iot_firewall_t","1") &&
    wr_iot_active_filter_apply_current())return 1;
 /* Close the permission gate even after a partially successful setter or
  * firewall reload. This best effort never substitutes for full recovery. */
 if(!nvram_set_int_temp("wr_iot_firewall_t",0) &&
    nvram_match("wr_iot_firewall_t","0") && wr_iot_policy_can_apply())
  start_firewall_ex();
 return 0;
}
#endif
