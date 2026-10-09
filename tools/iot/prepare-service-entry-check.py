#!/usr/bin/env python3
"""Extract actual installed DNS/DHCP entry wrappers for a private lock fixture."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
s=(a.source/'trunk/user/rc/services_ex.c').read_text(encoding='utf-8')
begin=s.index('#if defined(BOARD_WR1200JS)\nstatic int wr_iot_dns_lock(');end=s.index('\nint\nrestart_dns(void)',begin)
body=s[begin:end].replace('/var/run/wr-iot-services.lock','./service.lock')
pre=r"""
#define _GNU_SOURCE
#define BOARD_WR1200JS 1
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <assert.h>
#include "service-lock.h"
#include "service-guard.h"
static int gate=1,starts,stops,logs,invalid;
static const char *nvram_safe_get(const char *key){assert(!strcmp(key,"lan_ipaddr")||!strcmp(key,"lan_netmask"));return !strcmp(key,"lan_ipaddr")?"192.168.1.1":"255.255.255.0";}
static int wr_iot_dnsmasq(FILE *fp,int ap,const char *ip,const char *mask){assert(fp&&ap==0&&!strcmp(ip,"192.168.1.1")&&!strcmp(mask,"255.255.255.0"));return invalid?-1:1;}
static int nvram_get_int(const char *key){assert(!strcmp(key,"wr_iot_network_t"));return gate;}
static int get_ap_mode(void){return 0;}
static void logmessage(const char *a,const char *b){assert(a&&b);logs++;}
static int wr_iot_start_dns_raw(int ap){assert(ap==0);starts++;return 0;}
static void wr_iot_stop_dns_raw(void){stops++;}
"""
post=r"""
int main(void){char dir[]="/tmp/iot-service-entry-XXXXXX";struct wr_iot_service_lock held={-1};
 assert(mkdtemp(dir));assert(!chdir(dir));
 assert(start_dns_dhcpd(0)==0);stop_dns_dhcpd();assert(restart_dhcpd()==0);assert(starts==2&&stops==2);
 assert(wr_iot_service_lock_take(&held,"./service.lock"));
 assert(start_dns_dhcpd(0)==EBUSY);stop_dns_dhcpd();assert(restart_dhcpd()==EBUSY);assert(starts==2&&stops==2&&logs==3);
 wr_iot_service_lock_release(&held);assert(restart_dhcpd()==0);assert(starts==3&&stops==3);
 assert(wr_iot_service_guard_enter(1)==1);assert(wr_iot_service_guard_enter(1)==1);
 assert(!wr_iot_service_lock_take(&held,"./service.lock"));wr_iot_service_guard_leave(1);assert(!wr_iot_service_lock_take(&held,"./service.lock"));wr_iot_service_guard_leave(1);
 invalid=1;assert(restart_dhcpd()==EINVAL);assert(starts==3&&stops==3);
 assert(wr_iot_service_lock_take(&held,"./service.lock"));wr_iot_service_lock_release(&held);invalid=0;
 gate=0;assert(wr_iot_service_lock_take(&held,"./service.lock"));assert(start_dns_dhcpd(0)==0);stop_dns_dhcpd();assert(starts==4&&stops==4);wr_iot_service_lock_release(&held);
 assert(!unlink("service.lock"));assert(!chdir("/tmp"));assert(!rmdir(dir));
 puts("PASS actual RC gated entry serialization: start/stop/restart contention leaves raw callbacks untouched, restart avoids nested lock, OFF legacy path; invalid IoT preflight leaves existing daemon untouched and releases guard; other writers and daemon rollback pending");return 0;}
"""
a.output.write_text(pre+body+post,encoding='utf-8')
