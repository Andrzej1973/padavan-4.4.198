#!/usr/bin/env python3
"""Run actual ticket-aware command builders; allocator/transport ops injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
s=(a.candidate/'mcu/andes_mt.c').read_text()
names=('wr_iot_fw_command_alloc','wr_iot_fw_command_send','CmdRestartDLReq','CmdAddressLenReq','CmdFwScatter','CmdFwScatters','CmdFwStartReq')
parts=[]
for name in names:
 pos=s.index(name+'(');start=s.rfind('\n',0,pos)+1;end=s.index('\n}',pos)+2;parts.append(s[start:end])
prefix=r'''
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "mcu-boot-ticket.h"
typedef int INT32;typedef uint32_t UINT32;typedef unsigned char UINT8;
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define TRUE 1
#define FALSE 0
#define NDIS_STATUS_FAILURE 1
#define NDIS_STATUS_RESOURCES 8
#define P1_Q0 0
#define MT_RESTART_DL_REQ 0xef
#define MT_TARGET_ADDRESS_LEN_REQ 1
#define MT_PATCH_START_REQ 5
#define MT_FW_SCATTER 0xee
#define MT_FW_START_REQ 2
#define ROM_PATCH_START_ADDRESS 0x200
#define CMD_NA 0
#define EXT_CMD_NA 0
#define MT_UPLOAD_FW_UNIT 4096
#define CmdReStartDLRsp NULL
#define CmdAddrellLenRsp NULL
#define CmdStartDLRsp NULL
#define cpu2le32(v) (v)
#define DBGPRINT(level,args) do{if(0)printf args;}while(0)
typedef struct {int cmd_header_len;} RTMP_CHIP_CAP;
typedef struct {RTMP_CHIP_CAP chipCap;} RTMP_ADAPTER;
struct cmd_msg {unsigned capacity,used,command,wait,retry,route;unsigned char bytes[];};
static struct wr_iot_mcu_boot_ticket ticket;
static unsigned allocations,sends,ordinary,boot_calls,last_command,last_wait,last_retry,fail_alloc,fail_send;
static unsigned char payload[12],*scatter_data;static unsigned scatter_size,scatter_offset;
static struct cmd_msg *allocate(unsigned length,unsigned route){
 allocations++;if(fail_alloc)return NULL;
 struct cmd_msg *m=calloc(1,sizeof(*m)+length);assert(m);m->capacity=length;m->route=route;return m;
}
static struct cmd_msg *AndesAllocCmdMsg(RTMP_ADAPTER *ad,unsigned len){(void)ad;ordinary++;return allocate(len,0);}
static struct cmd_msg *wr_iot_mcu_boot_alloc(RTMP_ADAPTER *ad,unsigned len,const struct wr_iot_mcu_boot_ticket *t){(void)ad;assert(t==&ticket);boot_calls++;return allocate(len,1);}
void AndesForceFreeCmdMsg(struct cmd_msg *m){free(m);}
static void AndesInitCmdMsg(struct cmd_msg *m,unsigned pq,unsigned cmd,unsigned query,unsigned ext,unsigned wait,unsigned timeout,unsigned retry,unsigned rsp,unsigned len,char *data,void *handler){
 (void)pq;(void)query;(void)ext;(void)timeout;(void)rsp;(void)len;(void)data;(void)handler;
 m->command=cmd;m->wait=wait;m->retry=retry;
}
static void AndesAppendCmdMsg(struct cmd_msg *m,char *data,unsigned len){assert(m->used+len<=m->capacity);memcpy(m->bytes+m->used,data,len);m->used+=len;}
static int send_message(struct cmd_msg *m,unsigned route){
 assert(m->route==route);sends++;last_command=m->command;last_wait=m->wait;last_retry=m->retry;
 if(m->command==MT_FW_SCATTER){
  assert(scatter_data&&scatter_offset+m->used<=scatter_size);
  assert(!memcmp(m->bytes,scatter_data+scatter_offset,m->used));scatter_offset+=m->used;
 }else {assert(m->used<=sizeof(payload));memcpy(payload,m->bytes,m->used);}
 free(m);return sends==fail_send?7:0;
}
static int AndesSendCmdMsg(RTMP_ADAPTER *ad,struct cmd_msg *m){(void)ad;ordinary++;return send_message(m,0);}
static int wr_iot_mcu_boot_send(RTMP_ADAPTER *ad,struct cmd_msg *m,const struct wr_iot_mcu_boot_ticket *t){(void)ad;assert(t==&ticket);boot_calls++;return send_message(m,1);}
'''
tail=r'''
int main(void){
 RTMP_ADAPTER ad={.chipCap={32}};unsigned char image[9000];for(unsigned i=0;i<sizeof(image);i++)image[i]=i;
 for(unsigned owned=0;owned<2;owned++){
  const struct wr_iot_mcu_boot_ticket *t=owned?&ticket:NULL;
  allocations=sends=ordinary=boot_calls=fail_alloc=fail_send=0;
  assert(!CmdRestartDLReq(&ad,t)&&last_command==0xef&&last_wait&&!last_retry);
  assert(!CmdAddressLenReq(&ad,0x100,123,1,t)&&last_command==1&&last_wait&&!last_retry);
  UINT32 words[3];memcpy(words,payload,12);assert(words[0]==0x100&&words[1]==123&&words[2]==1);
  assert(!CmdFwStartReq(&ad,1,0x100,t)&&last_command==2&&last_wait&&!last_retry);
  memcpy(words,payload,8);assert(words[0]==1&&words[1]==0x100);
  scatter_data=image;scatter_size=sizeof(image);scatter_offset=0;
  unsigned before=sends;
  assert(!CmdFwScatters(&ad,image,sizeof(image),t)&&sends==before+3&&scatter_offset==sizeof(image)&&!last_wait&&!last_retry);
  assert((owned?!ordinary:!boot_calls));
  before=sends;fail_send=sends+2;scatter_offset=0;
  assert(CmdFwScatters(&ad,image,sizeof(image),t)==7&&sends==before+2&&scatter_offset==2*(4096-32));
  fail_send=0;fail_alloc=1;before=sends;
  assert(CmdFwStartReq(&ad,1,0x100,t)==8&&sends==before);fail_alloc=0;
  before=allocations;
  if(owned)assert(CmdAddressLenReq(&ad,ROM_PATCH_START_ADDRESS,123,1,t)==1&&allocations==before);
  else assert(!CmdAddressLenReq(&ad,ROM_PATCH_START_ADDRESS,123,1,t)&&last_command==MT_PATCH_START_REQ);
 }
 puts("PASS actual firmware builders: explicit boot/ordinary routing, payloads, scatter segmentation/error stop, allocation failure and boot ROM-patch refusal; transport injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-boot-builders-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+'\n'.join(parts)+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-sign-compare','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
