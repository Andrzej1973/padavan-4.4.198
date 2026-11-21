#!/usr/bin/env python3
"""Actual installed-source DNS state observer, external lock syscalls injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'restart-controller.inc').read_text()
start=source.index('int wr_iot_dns_activation_recovery_state(void)')
end=source.index('\nint wr_iot_dns_activation_abort',start)
prefix=r'''
#include <assert.h>
#include <stdio.h>
static int wr_iot_restart_active,wr_iot_restart_guard,wr_iot_restart_bound,wr_iot_restart_disabling;
static struct {struct {int active,lock;} transaction;} wr_iot_restart_state;
static int guard_valid=1,close_ok=1,lock_valid=1,closes;
#define WR_IOT_SERVICE_LOCK_PATH "/fixed/guard"
static int wr_iot_service_guard_dup(void){return guard_valid?10:-1;}
static int close(int fd){assert(fd==10);closes++;return close_ok?0:-1;}
static int wr_iot_service_lock_valid(const int *lock,const char *path){assert(lock&&path);return lock_valid;}
'''
tail=r'''
int main(void){
 assert(wr_iot_dns_activation_recovery_state()==0&&closes==1);
 wr_iot_restart_bound=1;assert(wr_iot_dns_activation_recovery_state()==-1);wr_iot_restart_bound=0;
 wr_iot_restart_guard=1;assert(wr_iot_dns_activation_recovery_state()==-1);
 wr_iot_restart_guard=0;wr_iot_restart_state.transaction.active=1;assert(wr_iot_dns_activation_recovery_state()==-1);
 wr_iot_restart_active=1;assert(wr_iot_dns_activation_recovery_state()==-1);
 wr_iot_restart_guard=1;assert(wr_iot_dns_activation_recovery_state()==1);
 wr_iot_restart_disabling=1;assert(wr_iot_dns_activation_recovery_state()==-1);wr_iot_restart_disabling=0;
 lock_valid=0;assert(wr_iot_dns_activation_recovery_state()==-1);lock_valid=1;
 close_ok=0;assert(wr_iot_dns_activation_recovery_state()==-1);close_ok=1;
 int prior=closes;guard_valid=0;assert(wr_iot_dns_activation_recovery_state()==-1&&closes==prior);
 puts("PASS actual DNS retained-state observer: absent/owned/unknown, disable/lock/guard/close refusal; no service mutation, lock syscalls injected");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='iot-dns-state-') as d:
    unit=Path(d)/'check.c';binary=Path(d)/'check';unit.write_text(prefix+source[start:end]+tail)
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(unit),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
