"""Actual fixed ra2 DOWN client; syscalls injected, no real router access."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>
#include "precreated-down-client.h"
static int fault,sockets,calls,closes;
static int fake_socket(int family,int type,int protocol){assert(family==AF_INET&&type==(SOCK_DGRAM|SOCK_CLOEXEC)&&!protocol);sockets++;return fault==1?-1:77;}
static int fake_close(int fd){assert(fd==77);closes++;return fault==3?-1:0;}
static int fake_ioctl(int fd,unsigned long op,struct ifreq *r){
 unsigned char id[16];assert(fd==77&&op==WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG&&!strcmp(r->ifr_name,"ra2"));calls++;
 assert(wr_iot_down_query_decode(id,(unsigned char*)r->ifr_data,64));
 if(fault==2)return -1;
 assert(wr_iot_down_reply_encode((unsigned char*)r->ifr_data,64,id,4,2,7));
 if(fault==4)r->ifr_data[8]^=1;
 if(fault==5)r->ifr_data[4]=WR_IOT_IDLE_REPLY;
 return 0;
}
#define socket fake_socket
#define ioctl fake_ioctl
#define close fake_close
#include "precreated-down-client.c"
int main(void){unsigned char id[16]={1},zero[16]={0};struct wr_iot_down_result out;
 assert(!wr_iot_driver_initial_down_read(zero,&out)&&!sockets);
 for(fault=0;fault<=5;fault++){
  sockets=calls=closes=0;out=(struct wr_iot_down_result){9,9,9};
  assert(wr_iot_driver_initial_down_read(id,&out)==!fault);
  assert(sockets==1&&calls==(fault!=1)&&closes==(fault!=1));
  if(fault)assert(!out.epoch&&!out.generation&&!out.main_close_serial);
  else assert(out.epoch==4&&out.generation==2&&out.main_close_serial==7);
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-down-client-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS fixed ra2 DOWN client: socket/ioctl/close/nonce/opcode failures clear output, one ioctl/close, zero nonce no socket; no router access')
