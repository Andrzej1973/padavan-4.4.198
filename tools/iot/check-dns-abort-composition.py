#!/usr/bin/env python3
"""Execute installed DNS abort/recover/finish with faulted resource adapters."""
from pathlib import Path
import subprocess, tempfile
here = Path(__file__).resolve().parent
source = (here / 'restart-controller.inc').read_text()
def function(signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]
prefix = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
static struct {struct {int active,lock;} transaction;} wr_iot_restart_state;
static int wr_iot_restart_active,wr_iot_restart_guard,wr_iot_restart_bound;
static int wr_iot_restart_prepared,wr_iot_restart_disabling;
static int wr_iot_restart_stopped_candidate,wr_iot_restart_old_running;
static unsigned wr_iot_restart_old_port,wr_iot_restart_old_dhcp_port;
static int wr_iot_restart_old_dhcp4;
static char wr_iot_restart_old_gateway[16];
static int wr_iot_restart_lease,wr_iot_restart_lease_generated;
static int wr_iot_restart_lease_captured,wr_iot_restart_lease_owned;
static int wr_iot_restart_lease_observed,wr_iot_restart_lease_restored;
static int fault,stops,restores,captures,launches,releases,running,guard_leaves;
#define WR_IOT_SERVICE_LOCK_PATH "fixture.lock"
#define WR_IOT_LEASE_PATH "fixture.leases"
static int wr_iot_service_guard_dup(void){return 10;}
static int close(int fd){assert(fd==10);return 0;}
static int wr_iot_service_lock_valid(const int *l,const char *p){assert(l&&p);return fault!=1;}
static void wr_iot_stop_dns_raw(void){stops++;running=0;}
static int wr_iot_restart_wait(int expected){return running==expected;}
static int wr_iot_service_state_recover(void *s,const char *p){assert(s&&p);restores++;return fault!=2;}
static int wr_iot_generated_capture(int *g,const char *p){assert(g&&p);captures++;return fault!=3;}
static int wr_iot_saved_restore(int *s,int *g,const char *p){assert(s&&g&&p);return fault!=4;}
static int is_dns_dhcpd_run(void){return running;}
static int eval(const char *p){assert(!strcmp(p,"/usr/sbin/dnsmasq"));launches++;if(fault==5)return 1;running=1;return 0;}
static int wr_iot_restart_service_wait(unsigned p,int d,unsigned dp,const char *g){(void)p;(void)d;(void)dp;(void)g;return fault!=6;}
static int wr_iot_writer_journal_unbind(void *t){assert(t);return fault!=7;}
static int wr_iot_service_state_finish(void *s,const char *p){assert(s&&p);if(fault==8)return 0;wr_iot_restart_state.transaction.active=0;return 1;}
static void wr_iot_saved_release(int *s){assert(s);releases++;}
static void wr_iot_service_guard_leave(int g){assert(g==1);guard_leaves++;}
'''
tail = r'''
int main(void){
 for(int failure=0;failure<=8;failure++){
  fault=failure;stops=restores=captures=launches=releases=guard_leaves=0;running=1;
  wr_iot_restart_active=wr_iot_restart_guard=wr_iot_restart_bound=wr_iot_restart_prepared=1;
  wr_iot_restart_state.transaction.active=1;wr_iot_restart_disabling=0;
  wr_iot_restart_stopped_candidate=0;wr_iot_restart_old_running=1;
  wr_iot_restart_lease_captured=wr_iot_restart_lease_owned=1;
  wr_iot_restart_lease_observed=wr_iot_restart_lease_restored=0;
  assert(wr_iot_dns_activation_recovery_state()==(failure==1?-1:1));
  if(failure){
   assert(!wr_iot_dns_activation_abort());
   assert(wr_iot_restart_active&&wr_iot_restart_guard&&wr_iot_restart_state.transaction.active);
   assert(!releases&&!guard_leaves);
   if(failure==1)assert(!stops&&!restores&&wr_iot_restart_prepared==0);
   if(failure==4)assert(captures==1&&wr_iot_restart_lease_observed);
   fault=0;
  }
  assert(wr_iot_dns_activation_abort());
  assert(wr_iot_dns_activation_recovery_state()==0&&running);
  assert(stops==1&&captures==(failure==3?2:1)&&releases==1&&guard_leaves==1);
  int old_stops=stops;assert(!wr_iot_dns_activation_abort()&&stops==old_stops);
 }
 puts("PASS actual DNS abort/recover/finish chain:8 resource faults, foreign lock refuses daemon stop, retained ownership/retry, successful lease identity retained across retries, guard released last; resource/daemon adapters injected");
}
'''
functions = '\n'.join(function(s) for s in (
    'static int wr_iot_restart_finish(void)',
    'static int wr_iot_restart_recover(void)',
    'int wr_iot_dns_activation_recovery_state(void)',
    'int wr_iot_dns_activation_abort(void)'))
with tempfile.TemporaryDirectory(prefix='iot-dns-abort-compose-') as d:
    unit = Path(d) / 'check.c'
    binary = Path(d) / 'check'
    unit.write_text(prefix + functions + tail)
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-pie','-no-pie',
                    str(unit),'-o',str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
