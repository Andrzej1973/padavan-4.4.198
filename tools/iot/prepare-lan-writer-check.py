#!/usr/bin/env python3
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
s=(a.source/'trunk/user/rc/net_lan.c').read_text(encoding='utf-8');body=''
for name in ['lan_up_manual','lan_up_auto','lan_down_auto']:
 begin=s.index('/* WR_IOT_LAN_WRAPPER_START '+name+' */');end=s.index('/* WR_IOT_LAN_WRAPPER_END '+name+' */',begin)
 body+=s[begin:end].replace('wr-iot/service-guard.h','service-guard.h')
pre=r"""
#define _GNU_SOURCE
#define BOARD_WR1200JS 1
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "service-lock.h"
#include "service-guard.h"
static int gate=1,manual,automatic,down,logs;
static int nvram_get_int(const char *k){assert(!strcmp(k,"wr_iot_network_t"));return gate;}
static void logmessage(const char *a,const char *b){assert(a&&b);logs++;}
static void wr_iot_lan_up_manual_raw(char *iface,char *domain){assert(iface&&domain);manual++;}
static void wr_iot_lan_up_auto_raw(char *iface,char *gateway,char *domain){assert(iface&&gateway&&domain);automatic++;}
static void wr_iot_lan_down_auto_raw(char *iface){assert(iface);down++;}
"""
post=r"""
int main(void){char dir[]="/tmp/iot-lan-writer-XXXXXX";struct wr_iot_service_lock held={-1};
 assert(mkdtemp(dir));assert(!chdir(dir));
 lan_up_manual("br0","local");lan_up_auto("br0","192.0.2.1","local");lan_down_auto("br0");assert(manual==1&&automatic==1&&down==1);
 assert(wr_iot_service_lock_take(&held,"./service.lock"));
 lan_up_manual("br0","local");lan_up_auto("br0","192.0.2.1","local");lan_down_auto("br0");assert(manual==1&&automatic==1&&down==1&&logs==3);wr_iot_service_lock_release(&held);
 assert(wr_iot_service_guard_enter(1)==1);lan_up_manual("br0","local");assert(manual==2);assert(!wr_iot_service_lock_take(&held,"./service.lock"));wr_iot_service_guard_leave(1);
 gate=0;assert(wr_iot_service_lock_take(&held,"./service.lock"));lan_down_auto("br0");assert(down==2);wr_iot_service_lock_release(&held);
 assert(!unlink("service.lock"));assert(!chdir("/tmp"));assert(!rmdir(dir));
 puts("PASS actual LAN DNS writer wrappers: busy prevents callbacks, nested call retains outer lock, OFF path preserved; caller retry and whole LAN lifecycle pending");return 0;}
"""
a.output.write_text(pre+body+post,encoding='utf-8')
