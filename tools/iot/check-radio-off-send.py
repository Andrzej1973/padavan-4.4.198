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
signature="INT32 wr_iot_send_radio_off_checked("
function=s.index(signature)
start=s.rfind("#ifdef RTMP_PCI_SUPPORT",0,function)
if start<0:
 start=function
function_end=s.index("\nINT32 CmdRadioOnOffCtrl(",function)
guard_end=s.find("#endif /* RTMP_PCI_SUPPORT */",function,function_end)
end=(guard_end+len("#endif /* RTMP_PCI_SUPPORT */") if guard_end>=0 else function_end)
fn=s[start:end]
hw=(a.candidate/'hw_ctrl/cmm_asic_mt.c').read_text()
code=r"""
#include <assert.h>
#include <stddef.h>
#define RTMP_PCI_SUPPORT 1
typedef int INT32;typedef struct {int unused;} RTMP_ADAPTER;
struct cmd_msg {int checked;};
#define NDIS_STATUS_FAILURE -1
#define NDIS_STATUS_RESOURCES -2
static int fail_alloc,result,sends;static struct cmd_msg message;
static struct cmd_msg *wr_iot_prepare_radio_off(RTMP_ADAPTER *ad){assert(ad);message.checked=1;return fail_alloc?NULL:&message;}
static INT32 AndesSendCmdMsg(RTMP_ADAPTER *ad,struct cmd_msg *msg){assert(ad&&msg->checked);sends++;return result;}
"""+fn+r"""
int main(void){RTMP_ADAPTER ad={0};
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
guard_start=hardware.index("#ifdef LOAD_FW_ONE_TIME",start)
guard_return=hardware.index("return FALSE;",guard_start)
guard_end=hardware.index("#endif",guard_return)
first_mutation=hardware.index("RTMP_IRQ_LOCK",start)
assert guard_start<guard_return<guard_end<first_mutation
print("PASS checked-send wrapper error propagation with LOAD_FW_ONE_TIME refusal preserved")
