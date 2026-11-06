#!/usr/bin/env python3
"""Exercise the retained SDK TX-power payload builder; no firmware/runtime claim."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('sdk', type=Path, help='complete pinned MT7603 SDK tree')
a = p.parse_args()
sdk = (a.sdk / 'include/mcu/andes_mt.h').read_text()
source = Path(__file__).parent / 'candidates/aux-remove-close-v39/mcu/andes_mt.c'
text = source.read_text()
start = text.index('VOID CmdSetTxPowerCtrl(')
body = text[start:text.index('\n}\n', start) + 3]
start = sdk.index('typedef struct _EXT_CMD_TX_POWER_CTRL_T')
wire = sdk[start:sdk.index(';', sdk.index('} EXT_CMD_TX_POWER_CTRL_T', start)) + 1]
defs = (a.sdk / 'include/eeprom/mt_e2p_def.h').read_text()
names = set(re.findall(r'\b(?:NIC_CONFIGURE_1(?:_TOP)?|TX[01]_G_BAND_\w+|TX_PWR_CCK_1_2M|G_BAND_20_40_BW_PWR_DELTA|STEP_NUM_NEG_7)\b', body))
constants = []
for name in sorted(names):
    match = re.search(r'^#define\s+' + name + r'\s+(0x[0-9a-fA-F]+|\d+)\b', defs, re.M)
    if not match:
        p.error('Missing pinned EEPROM constant: ' + name)
    constants.append('#define ' + name + ' ' + match.group(1))
prefix = r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
typedef unsigned char UINT8;typedef unsigned short USHORT;typedef void VOID;
struct MT_TX_PWR_CAP {unsigned pa_type;};
typedef struct {unsigned eeprom_type;unsigned char EEPROMImage[1024];struct {struct MT_TX_PWR_CAP MTTxPwrCap;} chipCap;struct {unsigned TxPowerPercentage;} CommonCfg;} RTMP_ADAPTER;
struct cmd_msg {unsigned unused;};static struct cmd_msg message;static unsigned sends,fail_alloc;
#define EEPROM_EFUSE 1
#define P1_Q0 0
#define EXT_CID 0xed
#define CMD_SET 1
#define EXT_CMD_SET_TX_POWER_CTRL 0x11
#define TRUE 1
#define NDIS_STATUS_RESOURCES 2
static void fixture_log(const char *format,...){(void)format;}
#define DBGPRINT(level,args) fixture_log args
#define NdisCopyMemory memcpy
#define RT28xx_EEPROM_READ16(ad,off,value) ((value)=(ad)->EEPROMImage[(off)]|((unsigned)(ad)->EEPROMImage[(off)+1]<<8))
static struct cmd_msg *AndesAllocCmdMsg(RTMP_ADAPTER *ad,unsigned size){(void)ad;assert(size==44);return fail_alloc?NULL:&message;}
static void AndesInitCmdMsg(struct cmd_msg *m,...){assert(m==&message);}
static unsigned char captured[44];
static void AndesAppendCmdMsg(struct cmd_msg *m,char *data,unsigned size){assert(m==&message&&size==44);memcpy(captured,data,size);}
static int AndesSendCmdMsg(RTMP_ADAPTER *ad,struct cmd_msg *m){assert(ad&&m==&message);sends++;return 0;}
static void EventExtCmdResult(void){}
'''
tail = r'''
int main(void){
 unsigned percentages[]={0,9,10,15,16,30,31,60,61,90,91,100};
 unsigned delta[]={12,12,9,9,6,6,3,3,1,1,0,0};
 for(unsigned mode=0;mode<2;mode++)for(unsigned n=0;n<12;n++){
  RTMP_ADAPTER ad={0};ad.eeprom_type=mode;ad.CommonCfg.TxPowerPercentage=percentages[n];
  for(unsigned i=0;i<sizeof(ad.EEPROMImage);i++)ad.EEPROMImage[i]=(unsigned char)i;
  sends=0;fail_alloc=0;CmdSetTxPowerCtrl(&ad,6);assert(sends==1);
  assert(captured[0]==6&&captured[3]==ad.EEPROMImage[TX0_G_BAND_TARGET_PWR]&&captured[4]==ad.EEPROMImage[TX1_G_BAND_TARGET_PWR]);
  assert(!memcmp(captured+5,ad.EEPROMImage+TX_PWR_CCK_1_2M,14));
  assert(captured[19]==ad.EEPROMImage[G_BAND_20_40_BW_PWR_DELTA]);
  assert(captured[1]==ad.EEPROMImage[NIC_CONFIGURE_1_TOP]&&captured[2]==ad.EEPROMImage[NIC_CONFIGURE_1]);
  unsigned offsets[]={TX0_G_BAND_OFFSET_LOW,TX0_G_BAND_CHL_PWR_DELTA_MID,TX0_G_BAND_OFFSET_HIGH,TX1_G_BAND_CHL_PWR_DELATE_LOW,TX1_G_BAND_CHL_PWR_DELTA_MID,TX1_G_BAND_CHL_PWR_DELTA_HIGH};
  for(unsigned i=0;i<6;i++)assert(captured[20+i]==ad.EEPROMImage[offsets[i]]);
  assert(!memcmp(captured+26,ad.EEPROMImage+STEP_NUM_NEG_7,17));assert(captured[43]==delta[n]);
  sends=0;fail_alloc=1;CmdSetTxPowerCtrl(&ad,6);assert(!sends);
 }
 puts("PASS actual SDK TX-power builder: 44-byte payload, EFUSE/image calibration, percentage boundaries, allocation refusal");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-tx-power-') as td:
    c = Path(td) / 'check.c'
    c.write_text(prefix + '\n' + '\n'.join(constants) + '\n' + wire + '\n' + body + tail)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function', '-fsanitize=address,undefined', '-fno-pie', '-no-pie', str(c), '-o', td+'/check'], check=True)
    subprocess.run([td+'/check'], check=True)
