#!/usr/bin/env python3
"""Exercise actual checked-send wrapper with injected message ownership."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("candidate",type=Path)
a=p.parse_args()
s=(a.candidate/"mcu/andes_mt.c").read_text()
start=s.index("INT32 wr_iot_send_radio_off_checked(")
end=s.index("\nINT32 CmdRadioOnOffCtrl(",start)
fn=s[start:end]
hw=(a.candidate/'hw_ctrl/cmm_asic_mt.c').read_text()
mask=next(line.strip() for line in hw.splitlines() if 'Value &= ~(1U << 1);' in line)
fn += '\nstatic unsigned clear_bit(unsigned Value){'+mask+'return Value;}\n'
code=r"""
#include <assert.h>
#include <stddef.h>
typedef int INT32;typedef struct {int unused;} RTMP_ADAPTER;
struct cmd_msg {int checked;};
#define NDIS_STATUS_FAILURE -1
#define NDIS_STATUS_RESOURCES -2
static int fail_alloc,result,sends;static struct cmd_msg message;
static struct cmd_msg *wr_iot_prepare_radio_off(RTMP_ADAPTER *ad){assert(ad);message.checked=1;return fail_alloc?NULL:&message;}
static INT32 AndesSendCmdMsg(RTMP_ADAPTER *ad,struct cmd_msg *msg){assert(ad&&msg->checked);sends++;return result;}
"""+fn+r"""
int main(void){RTMP_ADAPTER ad={0}; unsigned i; const unsigned upper[]={0U,0x12340000U,0xffff0000U,0x80000000U}; unsigned k; for(k=0;k<4;k++)for(i=0;i<65536;i++){unsigned v=upper[k]|i,r=clear_bit(v);assert((r^v)==(v&2U));assert((r&0xffff0000U)==upper[k]);}
assert(wr_iot_send_radio_off_checked(NULL)==-1&&!sends);
fail_alloc=1;assert(wr_iot_send_radio_off_checked(&ad)==-2&&!sends);
fail_alloc=0;result=-9;assert(wr_iot_send_radio_off_checked(&ad)==-9&&sends==1);
result=0;assert(wr_iot_send_radio_off_checked(&ad)==0&&sends==2);
return 0;}
"""
with tempfile.TemporaryDirectory(prefix="wr-radio-send-") as directory:
 root=Path(directory);source=root/"check.c";binary=root/"check";source.write_text(code)
 subprocess.run(["gcc","-std=c11","-Wall","-Wextra","-Werror","-fsanitize=address,undefined",str(source),"-o",str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
hardware=(a.candidate/"hw_ctrl/cmm_asic_mt.c").read_text()
start=hardware.index("BOOLEAN wr_iot_mt_radio_off_checked(")
assert "if (wr_iot_send_radio_off_checked(pAd) != NDIS_STATUS_SUCCESS)" in hardware[start:]
assert "#ifdef LOAD_FW_ONE_TIME\n /* This build uses an AGG_TEMP write without an MCU result. */\n return FALSE;" in hardware[start:]
print("PASS checked-send wrapper error propagation and retained firmware-policy guard")

# Exhaustively preserve low bits and representative radio-request high bits.
assert 'Value &= (0<<1);' not in hardware
assert hardware.count('Value &= ~(1U << 1);') == 1
print('PASS AGG_TEMP bit-1 mask preserves all unrelated bits; no concurrency claim')
