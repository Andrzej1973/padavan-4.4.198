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
body='#pragma GCC diagnostic ignored "-Wdeclaration-after-statement"\n#pragma GCC diagnostic push\n#pragma GCC diagnostic error "-Wdeclaration-after-statement"\n'+body+'\n#pragma GCC diagnostic pop\n'
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
 if(phase==4)return fault==7?~0u:fault==5?1:2;
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
if 'wr_iot_fw_command_alloc' in s:
 prefix=prefix.replace('#define RTMP_PCI_SUPPORT 1',
                       '#define RTMP_PCI_SUPPORT 1\n#define MT_MAC 1\n#include "mcu-boot-ticket.h"')
 prefix=prefix.replace('int FWLoad;} RTMP_ADAPTER;',
                       'int FWLoad;unsigned wr_iot_boot_active;struct wr_iot_mcu_boot_ticket wr_iot_boot_ticket;} RTMP_ADAPTER;')
 for old in ('CmdRestartDLReq(RTMP_ADAPTER *ad)',
             'CmdAddressLenReq(RTMP_ADAPTER *ad,unsigned addr,unsigned len,unsigned flags)',
             'CmdFwScatters(RTMP_ADAPTER *ad,unsigned char *image,unsigned len)',
             'CmdFwStartReq(RTMP_ADAPTER *ad,unsigned mode,unsigned addr)'):
  assert prefix.count(old)==1
  prefix=prefix.replace(old,old[:-1]+',const struct wr_iot_mcu_boot_ticket *boot)')
 prefix=prefix.replace('(void)ad;',
     '(void)ad;assert(boot==(ad->wr_iot_boot_active?&ad->wr_iot_boot_ticket:NULL));')
 tail=tail.replace('for(warm=0;warm<2;warm++)',
                   'for(unsigned owned=0;owned<2;owned++)for(warm=0;warm<2;warm++)')
 tail=tail.replace('RTMP_ADAPTER ad={0};', 'RTMP_ADAPTER ad={0};ad.wr_iot_boot_active=owned;')
if 'wr_iot_mcu_boot_rom_observe(' in body:
 prefix+=r'''
static unsigned observed,observe_fail;
static int wr_iot_mcu_boot_rom_observe(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *boot,unsigned acked){
 assert(ad->wr_iot_boot_active&&boot==&ad->wr_iot_boot_ticket&&acked==(unsigned)warm);observed++;return observe_fail?1:0;
}
'''
 tail=tail.replace('ad.MCUCtrl.Stage=9;', 'observed=0;ad.MCUCtrl.Stage=9;')
 tail=tail.replace('assert(writes>=7);','assert(observed==(unsigned)(owned&&fault!=1&&fault!=6));assert(writes>=7);')
 anchor=' puts("PASS actual reload Method1:';pos=tail.index(anchor)
 tail=tail[:pos]+r'''
 RTMP_ADAPTER failed_observation={0};failed_observation.wr_iot_boot_active=1;
 failed_observation.chipCap.fw_header_image=image;failed_observation.chipCap.fw_len=sizeof(image);
 warm=fault=phase=addresses=scatters=starts=observed=0;observe_fail=1;
 assert(AndesMTLoadFwMethod1(&failed_observation)==1&&observed==1&&!addresses&&!scatters&&!starts);
 observe_fail=0;
'''+tail[pos:]
if 'wr_iot_mcu_boot_hardware_prepare(' in body:
 prefix+=r'''
static unsigned bind_fail,hardware_calls,thaw_calls,abort_calls;
static int wr_iot_mcu_boot_hardware_prepare(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){assert(ad&&t&&observed);hardware_calls++;return bind_fail==1?7:0;}
static int wr_iot_mcu_boot_thaw(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){assert(ad&&t&&observed);thaw_calls++;return bind_fail==2?7:0;}
static int wr_iot_mcu_boot_loader_abort(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){assert(ad&&t);abort_calls++;return 0;}
'''
 tail=tail.replace('assert(writes>=7);','if(!owned||!fault)assert(writes>=7);')
 anchor=' puts("PASS actual reload Method1:';pos=tail.index(anchor)
 tail=tail[:pos]+r'''
 for(bind_fail=1;bind_fail<=2;bind_fail++){
  RTMP_ADAPTER ad={0};ad.wr_iot_boot_active=1;
  ad.chipCap.fw_header_image=image;ad.chipCap.fw_len=sizeof(image);
  warm=fault=phase=addresses=scatters=starts=observed=hardware_calls=thaw_calls=abort_calls=0;
  assert(AndesMTLoadFwMethod1(&ad)==7&&ad.MCUCtrl.Stage==FW_NO_INIT);
  assert(hardware_calls==1&&thaw_calls==(bind_fail==2)&&abort_calls==1);
  assert(!addresses&&!scatters&&!starts);
 }
 bind_fail=0;
'''+tail[pos:]
 if 'wr_iot_mcu_boot_loader_abort(' in body:
  pos=tail.index(' puts("PASS actual reload Method1:')
  tail=tail[:pos]+r'''
 for(unsigned owned=0;owned<2;owned++){
  RTMP_ADAPTER ad={0};ad.wr_iot_boot_active=owned;
  ad.chipCap.fw_header_image=image;ad.chipCap.fw_len=sizeof(image);
  warm=phase=addresses=scatters=starts=observed=abort_calls=0;fault=7;
  assert(AndesMTLoadFwMethod1(&ad)==1&&ad.MCUCtrl.Stage==FW_NO_INIT);
  assert(starts==1&&abort_calls==owned);
 }
 fault=0;
'''+tail[pos:]
if 'wr_iot_mcu_boot_firmware_receipt(' in body:
 prefix+=r'''
static unsigned receipt_fail,receipt_calls,receipt_writes;
static int wr_iot_mcu_boot_firmware_receipt(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){
 assert(ad&&t&&starts==1&&phase==4&&ad->MCUCtrl.Stage==FW_RUN_TIME);
 receipt_calls++;receipt_writes=writes;return receipt_fail?9:0;
}
'''
 pos=tail.index(' puts("PASS actual reload Method1:')
 tail=tail[:pos]+r'''
 for(warm=0;warm<2;warm++)for(receipt_fail=0;receipt_fail<2;receipt_fail++){
  RTMP_ADAPTER ad={0};ad.wr_iot_boot_active=1;
  ad.chipCap.fw_header_image=image;ad.chipCap.fw_len=sizeof(image);
  fault=phase=addresses=scatters=starts=observed=abort_calls=receipt_calls=0;
  assert(AndesMTLoadFwMethod1(&ad)==(receipt_fail?9:0));
  assert(receipt_calls==1&&abort_calls==receipt_fail);
  assert(ad.MCUCtrl.Stage==(receipt_fail?FW_NO_INIT:FW_RUN_TIME));
  if(receipt_fail)assert((unsigned)writes==receipt_writes);
 }
 receipt_fail=0;
 puts("PASS Method1 receipt binding: cold/warm FW_START plus RUN precede receipt; receipt failure aborts before generic SCH cleanup");
'''+tail[pos:]
with tempfile.TemporaryDirectory(prefix='wr-fw-method1-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+body+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
if 'wr_iot_fw_command_alloc' in s:
 one_time_tail=r'''
int main(void){
 unsigned char image[64]={0};RTMP_ADAPTER ad={0};
 ad.chipCap.fw_header_image=image;ad.chipCap.fw_len=sizeof(image);
 for(warm=0;warm<2;warm++){
  ad.wr_iot_boot_active=1;phase=addresses=scatters=starts=restarts=writes=delays=0;
  assert(AndesMTLoadFwMethod1(&ad)==NDIS_STATUS_FAILURE);
  assert(!addresses&&!scatters&&!starts&&!restarts&&!writes);
 }
 ad.wr_iot_boot_active=0;warm=1;fault=phase=0;
 assert(!AndesMTLoadFwMethod1(&ad)&&ad.FWLoad==1&&ad.MCUCtrl.Stage==FW_RUN_TIME);
 assert(!addresses&&!scatters&&!starts&&!restarts);
 puts("PASS actual LOAD_FW_ONE_TIME Method1 refuses boot lease before MMIO and preserves ordinary warm-firmware path");
}
'''
 with tempfile.TemporaryDirectory(prefix='wr-fw-method1-once-') as td:
  c=Path(td)/'check.c';c.write_text('#define LOAD_FW_ONE_TIME 1\n'+prefix+body+one_time_tail)
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
  subprocess.run([td+'/check'],check=True)
