#!/usr/bin/env python3
"""Execute actual Method1 loader with injected command/MMIO failures; no hardware."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
s=(a.candidate/'mcu/andes_mt.c').read_text()
start=s.index('static NDIS_STATUS AndesMTLoadFwMethod1(')
body=s[start:s.index('static NDIS_STATUS AndesMTLoadFwMethod2(',start)]
prefix=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint32_t UINT32;typedef int NDIS_STATUS;
#define RTMP_PCI_SUPPORT 1
#define BIN_FILE_METHOD 1
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define FW_NO_INIT 0
#define FW_DOWNLOAD 1
#define FW_RUN_TIME 2
#define FW_CODE_START_ADDRESS1 0x100
#define TARGET_ADDR_LEN_NEED_RSP 1
#define TOP_MISC2 0x1134
#define MCU_PCIE_REMAP_1 0x200
#define SCH_REG4 0x300
#define SCH_REG4_BYPASS_MODE_MASK 1u
#define SCH_REG4_FORCE_QID_MASK 0xf0u
#define SCH_REG4_BYPASS_MODE(v) (v)
#define SCH_REG4_FORCE_QID(v) ((v)<<4)
#define GET_REMAP_1_BASE(v) 0u
#define GET_REMAP_1_OFFSET(v) 0u
#define IS_MT7603(ad) ((void)(ad),1)
#define DBGPRINT(level,args) ((void)0)
#define OS_LOAD_CODE_FROM_BIN(img,name,dev,len) ((void)(img),(void)(name),(void)(dev),(void)(len))
typedef struct {void *pci_dev;} *POS_COOKIE;
typedef struct {int load_code_method;unsigned char *FWImageName,*fw_header_image;unsigned fw_len;char *fw_bin_file_name;} RTMP_CHIP_CAP;
struct MCU_CTRL {int Stage;};
typedef struct {RTMP_CHIP_CAP chipCap;void *OS_Cookie;struct MCU_CTRL MCUCtrl;int FWLoad;} RTMP_ADAPTER;
static int fault,phase,warm,restarts,addresses,scatters,starts,writes,delays;
static unsigned read_register(unsigned reg){
 if(reg!=TOP_MISC2)return 0;
 if(phase==4)return fault==5?1:2;
 if(!phase&&warm)return 2;
 return fault==1?0:1;
}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),(*(out))=read_register(reg))
#define RTMP_IO_WRITE32(ad,reg,value) ((void)(ad),(void)(reg),(void)(value),writes++)
#define RtmpusecDelay(value) ((void)(value))
#define RtmpOsMsDelay(value) ((void)(value),delays++)
static int CmdRestartDLReq(RTMP_ADAPTER *ad){(void)ad;phase=1;restarts++;return fault==6?7:0;}
static int CmdAddressLenReq(RTMP_ADAPTER *ad,unsigned addr,unsigned len,unsigned flags){
 (void)ad;assert(addr==FW_CODE_START_ADDRESS1&&len==4&&flags==1);phase=2;addresses++;return fault==2?7:0;
}
static int CmdFwScatters(RTMP_ADAPTER *ad,unsigned char *image,unsigned len){
 (void)ad;assert(image&&len==4);phase=3;scatters++;return fault==3?7:0;
}
static int CmdFwStartReq(RTMP_ADAPTER *ad,unsigned mode,unsigned addr){
 (void)ad;assert(mode==1&&addr==FW_CODE_START_ADDRESS1);phase=4;starts++;return fault==4?7:0;
}
'''
tail=r'''
int main(void){
 unsigned char image[64]={0};
 for(warm=0;warm<2;warm++)for(fault=0;fault<=6;fault++){
  if(fault==6&&!warm)continue;
  RTMP_ADAPTER ad={0};ad.chipCap.fw_header_image=image;ad.chipCap.fw_len=sizeof(image);
  ad.MCUCtrl.Stage=9;phase=restarts=addresses=scatters=starts=writes=delays=0;
  int result=AndesMTLoadFwMethod1(&ad);
  assert(result==(fault?fault==1||fault==5?1:7:0));
  assert(ad.MCUCtrl.Stage==(fault?FW_NO_INIT:FW_RUN_TIME));
  assert(restarts==warm&&addresses==(fault!=1&&fault!=6));
  assert(scatters==(fault!=1&&fault!=2&&fault!=6));
  assert(starts==(fault==0||fault==4||fault==5));
  assert(writes>=7); /* Existing common cleanup still executes. */
  if(fault==4)assert(!delays); /* Start NACK cannot poll into success. */
 }
 puts("PASS actual reload Method1: cold/warm start, ROM timeout, address/scatter/start errors, run timeout; command/MMIO operations injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-fw-method1-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+body+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
