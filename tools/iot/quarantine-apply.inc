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
#endif
