/* Fixed files written by start_dns_dhcpd and its helpers. Caller holds transaction lock. */
#ifndef WR_IOT_DNSMASQ_FILES_H
#define WR_IOT_DNSMASQ_FILES_H
#include "saved-bundle.h"
#ifndef WR_IOT_DNSMASQ_FIXTURE_ROOT
#define WR_IOT_DNSMASQ_FIXTURE_ROOT ""
#endif
static inline int wr_iot_dnsmasq_files_capture(struct wr_iot_saved_bundle *out){
 static const char *const paths[]={
 WR_IOT_DNSMASQ_FIXTURE_ROOT "/etc/dnsmasq.conf",
 WR_IOT_DNSMASQ_FIXTURE_ROOT "/etc/dnsmasq/dhcp/dhcp-hosts.rc",
 WR_IOT_DNSMASQ_FIXTURE_ROOT "/etc/ethers",
 WR_IOT_DNSMASQ_FIXTURE_ROOT "/tmp/hosts.static",
 WR_IOT_DNSMASQ_FIXTURE_ROOT "/etc/hostname",
 WR_IOT_DNSMASQ_FIXTURE_ROOT "/etc/hosts",
 WR_IOT_DNSMASQ_FIXTURE_ROOT "/tmp/dnsmasq.servers",
 WR_IOT_DNSMASQ_FIXTURE_ROOT "/etc/resolv.conf"
 };
 return wr_iot_bundle_capture(out,paths,sizeof(paths)/sizeof(paths[0]));
}
#endif
