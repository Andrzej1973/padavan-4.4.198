#!/usr/bin/env python3
"""Execute pinned Guest field classification and full notification dispatcher."""
import hashlib
import re
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

here = Path(__file__).resolve().parent
with tarfile.open(sys.argv[1]) as archive:
    source = archive.extractfile('trunk/user/httpd/web_ex.c').read().decode()

def block(start):
    brace = source.index('{', start)
    end = brace + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]

classifiers = []
validation = block(source.index('validate_asp_apply(webs_t'))
for band in ('rt', 'wl'):
    marker = 'else if (!strcmp(v->name, "' + band + '_guest_enable") ||'
    assert source.count(marker) == 1
    actual = block(source.index(marker))
    expected = {band + '_guest_' + field for field in ('enable', 'date_x', 'time_x', 'time2_x')}
    assert set(re.findall(r'"([rw][tl]_guest_[^"]+)"', actual)) == expected
    assert set(re.findall(r'"(' + band + r'_guest_[^"]+)"', validation)) == expected
    fallback = 'else\n\t\t\t{\n\t\t\t\t' + band + '_modified |= WIFI_COMMON_CHANGE_BIT;\n\t\t\t}'
    assert validation.count(fallback) == 1
    fallback = fallback.replace(band + '_modified', 'flags')
    actual = actual.replace('else if', 'if', 1).replace('v->name', 'name').replace(band + '_modified', 'flags')
    classifiers.append('static int classify_' + band + '(const char *name){int flags=0;\n' + actual + '\n' + fallback + '\nreturn flags;}\n')

dispatcher = block(source.index('ej_notify_services(int'))
fixture = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned long long u64;
typedef FILE *webs_t;
#define BOARD_HAS_5G_RADIO 1
#define WIFI_GUEST_CONTROL_BIT 1
#define WIFI_COMMON_CHANGE_BIT 2
#define WIFI_IWPRIV_CHANGE_BIT 4
#define WIFI_RADIO_CONTROL_BIT 8
#define WIFI_SCHED_CONTROL_BIT 16
#define EVM_RESTART_WIFI2 1ULL
#define EVM_RESTART_WIFI5 2ULL
#define EVM_RESTART_REBOOT 4ULL
#define RCN_RESTART_WIFI2 "restart2-fixture"
#define RCN_RESTART_WIFI5 "restart5-fixture"
#define dbG(...) ((void)0)
static u64 restart_needed_bits;
static int rt_modified,wl_modified,calls;
static const char *observed;
static struct {const char *notify_cmd;u64 event_mask,event_unmask;} events_desc[]={{NULL,0,0}};
static int nvram_get_int(const char *name){assert(!strcmp(name,"nvram_manual"));return 0;}
static void nvram_commit(void){abort();}
static void sys_reboot(void){abort();}
static void nvram_set_int_temp(const char *name,int value){(void)name;(void)value;abort();}
static void notify_rc(const char *name){calls++;observed=name;}
'''
main = r'''
int main(void){
 const char *fields[]={"enable","ssid","closed","auth_mode","wpa_mode","crypto","lan_isolate","ap_isolate","macrule","mcs_mode","date_x","time_x","time2_x","wpa_psk"};
 for(int band=0;band<2;band++)for(unsigned int i=0;i<14;i++){
  char name[64];snprintf(name,sizeof(name),"%s_guest_%s",band?"wl":"rt",fields[i]);
  int expected=(i==0||i==10||i==11||i==12)?WIFI_GUEST_CONTROL_BIT:WIFI_COMMON_CHANGE_BIT;
  int flags=band?classify_wl(name):classify_rt(name);assert(flags==expected);
  restart_needed_bits=band?EVM_RESTART_WIFI5:EVM_RESTART_WIFI2;
  rt_modified=band?0:flags;wl_modified=band?flags:0;calls=0;observed=NULL;
  assert(!ej_notify_services(0,NULL,0,NULL));assert(calls==1&&!restart_needed_bits&&!rt_modified&&!wl_modified);
  assert(!strcmp(observed,expected==WIFI_COMMON_CHANGE_BIT?(band?RCN_RESTART_WIFI5:RCN_RESTART_WIFI2):(band?"control_wifi_guest_wl":"control_wifi_guest_rt")));
 }
 for(int band=0;band<2;band++){
  restart_needed_bits=band?EVM_RESTART_WIFI5:EVM_RESTART_WIFI2;
  rt_modified=band?0:3;wl_modified=band?3:0;calls=0;
  assert(!ej_notify_services(0,NULL,0,NULL));assert(calls==1);
  assert(!strcmp(observed,band?RCN_RESTART_WIFI5:RCN_RESTART_WIFI2));
 }
 puts("PASS actual vendor classifier/notification dispatcher: 4 control-only fields, other10 request full radio restart per band; common dominates mixed request; RC execution/runtime unverified");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-guest-notify-policy-') as scratch:
    root = Path(scratch)
    (root / 'fixture.c').write_text(fixture + ''.join(classifiers) + '\n#pragma GCC diagnostic push\n#pragma GCC diagnostic ignored "-Wunused-parameter"\nstatic int\n' + dispatcher + '\n#pragma GCC diagnostic pop\n' + main)
    subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined', '-fno-pie', '-no-pie', str(root / 'fixture.c'), '-o', str(root / 'fixture')], check=True)
    subprocess.run([str(root / 'fixture')], check=True)
    print('Owned scratch bytes removed', sum(p.stat().st_size for p in root.iterdir()))
assert not root.exists()
print('Pinned HTTP source SHA256', hashlib.sha256(source.encode()).hexdigest())
