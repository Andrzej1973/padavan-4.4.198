#!/usr/bin/env python3
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();body=''
for file,name in [('net_lan.c','full_restart_lan'),('net6.c','full_restart_ipv6')]:
 s=(a.source/'trunk/user/rc'/file).read_text(encoding='utf-8');begin=s.index('/* WR_IOT_SEQUENCE_START '+name+' */');end=s.index('/* WR_IOT_SEQUENCE_END '+name+' */',begin);body+=s[begin:end].replace('wr-iot/service-guard.h','service-guard.h')
pre=r"""
#define _GNU_SOURCE
#define BOARD_WR1200JS 1
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "service-lock.h"
#include "service-guard.h"
static int gate=1,lan_calls,six_calls,logs;
static int nvram_get_int(const char *k){assert(!strcmp(k,"wr_iot_network_t"));return gate;}
static void logmessage(const char *a,const char *b){assert(a&&b);logs++;}
static void check_nested(void){struct wr_iot_service_lock other={-1};int token=wr_iot_service_guard_enter(gate);assert(token);if(gate)assert(!wr_iot_service_lock_take(&other,"./service.lock"));wr_iot_service_guard_leave(token);}
static void wr_iot_full_restart_lan_raw(void){check_nested();lan_calls++;}
static void wr_iot_full_restart_ipv6_raw(int old){assert(old==0);check_nested();six_calls++;}
"""
post=r"""
int main(void){char dir[]="/tmp/iot-sequence-XXXXXX";struct wr_iot_service_lock held={-1};
 assert(mkdtemp(dir));assert(!chdir(dir));full_restart_lan();full_restart_ipv6(0);assert(lan_calls==1&&six_calls==1);
 assert(wr_iot_service_lock_take(&held,"./service.lock"));full_restart_lan();full_restart_ipv6(0);assert(lan_calls==1&&six_calls==1&&logs==2);wr_iot_service_lock_release(&held);
 assert(wr_iot_service_guard_enter(1)==1);full_restart_lan();full_restart_ipv6(0);assert(lan_calls==2&&six_calls==2);assert(!wr_iot_service_lock_take(&held,"./service.lock"));wr_iot_service_guard_leave(1);
 gate=0;assert(wr_iot_service_lock_take(&held,"./service.lock"));full_restart_ipv6(0);assert(six_calls==3);wr_iot_service_lock_release(&held);
 assert(!unlink("service.lock"));assert(!chdir("/tmp"));assert(!rmdir(dir));puts("PASS installed full LAN/IPv6 sequence wrappers: external lock blocks callbacks, nested calls retain outer lock, OFF path preserved; raw service recovery pending");return 0;}
"""
a.output.write_text(pre+body+post,encoding='utf-8')
