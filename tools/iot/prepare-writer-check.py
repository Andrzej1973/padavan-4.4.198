#!/usr/bin/env python3
"""Extract installed writer wrappers, not their file-generating bodies."""
import argparse,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
body=''
for file,names in [('services_ex.c',['fill_dnsmasq_servers']),('net_wan.c',['update_resolvconf','update_hosts_router'])]:
 s=(a.source/'trunk/user/rc'/file).read_text(encoding='utf-8')
 for name in names:
  begin=s.index('/* WR_IOT_WRITE_WRAPPER_START '+name+' */');end=s.index('/* WR_IOT_WRITE_WRAPPER_END '+name+' */',begin)
  body+=s[begin:end].replace('wr-iot/service-guard.h','service-guard.h')
pre=r"""
#define _GNU_SOURCE
#define BOARD_WR1200JS 1
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <assert.h>
#include "service-lock.h"
#include "service-guard.h"
static int gate=1,servers,resolv,hosts;
static int nvram_get_int(const char *key){assert(!strcmp(key,"wr_iot_network_t"));return gate;}
int fill_dnsmasq_servers(void);
static int wr_iot_fill_dnsmasq_servers_raw(void){servers++;return 7;}
static int wr_iot_update_resolvconf_raw(int first,int notify){assert(first==0&&notify==1);resolv++;assert(fill_dnsmasq_servers()==7);return 8;}
static int wr_iot_update_hosts_router_raw(const char *ip){assert(!strcmp(ip,"192.0.2.1"));hosts++;return 9;}
"""
post=r"""
int main(void){char dir[]="/tmp/iot-writer-XXXXXX";struct wr_iot_service_lock held={-1};
 assert(mkdtemp(dir));assert(!chdir(dir));
 assert(fill_dnsmasq_servers()==7);assert(update_resolvconf(0,1)==8);assert(update_hosts_router("192.0.2.1")==9);assert(servers==2&&resolv==1&&hosts==1);
 assert(wr_iot_service_lock_take(&held,"./service.lock"));assert(fill_dnsmasq_servers()==EBUSY);assert(update_resolvconf(0,1)==EBUSY);assert(update_hosts_router("192.0.2.1")==EBUSY);assert(servers==2&&resolv==1&&hosts==1);wr_iot_service_lock_release(&held);
 assert(update_resolvconf(0,1)==8);assert(servers==3&&resolv==2);
 gate=0;assert(wr_iot_service_lock_take(&held,"./service.lock"));assert(update_hosts_router("192.0.2.1")==9);wr_iot_service_lock_release(&held);
 assert(!unlink("service.lock"));assert(!chdir("/tmp"));assert(!rmdir(dir));
 puts("PASS actual installed WAN DNS/hosts/server writer wrappers: nested call succeeds, contention prevents raw writer calls, return values and OFF legacy path preserved; actual writer body/rollback still pending");return 0;}
"""
a.output.write_text(pre+body+post,encoding='utf-8')
