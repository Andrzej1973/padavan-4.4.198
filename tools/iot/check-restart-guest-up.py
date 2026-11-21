#!/usr/bin/env python3
"""Fixed Guest UP/DOWN transport; no automatic retry or readiness inference."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <stdarg.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <string.h>
#include <unistd.h>
static int socket_error,get_error,set_error,close_error,already_up,gets,sets,closes,main_down,down_test;
static int fake_socket(int d,int t,int p){assert(d==AF_INET&&t==(SOCK_DGRAM|SOCK_CLOEXEC)&&!p);return socket_error?-1:9;}
static int fake_ioctl(int fd,unsigned long cmd,...){
 assert(fd==9);va_list args;va_start(args,cmd);struct ifreq*r=va_arg(args,struct ifreq*);va_end(args);
 if(cmd==SIOCGIFFLAGS){
  gets++;
  if(!strcmp(r->ifr_name,"ra0")){r->ifr_flags=main_down?0:IFF_UP;return get_error?-1:0;}
  assert(!strcmp(r->ifr_name,"ra1"));r->ifr_flags=(short)(IFF_BROADCAST|(already_up?IFF_UP:0));return get_error?-1:0;
 }
 assert(!strcmp(r->ifr_name,"ra1"));
 assert(cmd==SIOCSIFFLAGS&&r->ifr_flags==(down_test?IFF_BROADCAST:(IFF_BROADCAST|IFF_UP)));sets++;return set_error?-1:0;
}
static int fake_close(int fd){assert(fd==9);closes++;return close_error?-1:0;}
#define socket fake_socket
#define ioctl fake_ioctl
#define close fake_close
#include "restart-guest-up.c"
int main(void){
 for(int fault=0;fault<7;fault++){
  main_down=fault==6;socket_error=fault==1;get_error=fault==2;already_up=fault==3;set_error=fault==4;close_error=fault==5;gets=sets=closes=0;
  enum wr_iot_restart_up_result r=wr_iot_restart_guest_up();
  assert(r==((fault>=1&&fault<=3)||fault==6?WR_RESTART_UP_NOT_SUBMITTED:fault>=4?WR_RESTART_UP_UNCERTAIN:WR_RESTART_UP_RETURNED));
  assert(sets==((fault>=1&&fault<=3)||fault==6?0:1));assert(gets==(fault==1?0:fault==2||fault==6?1:2));assert(closes==(fault==1?0:1));
 }
 socket_error=get_error=set_error=close_error=main_down=0;already_up=1;
 int observed=77;assert(wr_iot_restart_guest_admin_state(&observed)&&observed==1);
 close_error=1;observed=77;assert(!wr_iot_restart_guest_admin_state(&observed)&&observed==77);close_error=0;
 socket_error=1;assert(!wr_iot_restart_guest_admin_state(&observed)&&observed==77);socket_error=0;
 already_up=0;assert(wr_iot_restart_guest_admin_state(&observed)&&!observed);
 down_test=1;
 for(int fault=0;fault<6;fault++){
  socket_error=fault==1;get_error=fault==2;already_up=fault!=3;
  set_error=fault==4;close_error=fault==5;gets=sets=closes=0;
  enum wr_iot_restart_up_result result=wr_iot_restart_guest_down();
  assert(result==(fault==1||fault==2?WR_RESTART_UP_NOT_SUBMITTED:fault>=4?WR_RESTART_UP_UNCERTAIN:WR_RESTART_UP_RETURNED));
  assert(sets==(fault==0||fault>=4?1:0));
  assert(gets==(fault==1?0:1));assert(closes==(fault==1?0:1));
 }
 puts("PASS fixed Guest ra1 UP transport: Main ra0 UP required, GETFLAGS then one SETFLAGS preserving other flags, socket/get/alreadyUP/MainDOWN not submitted, set/close uncertain, no internal retry or readiness claim; syscalls injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-guest-up-') as d:
 unit=Path(d)/'check.c';unit.write_text(code);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
