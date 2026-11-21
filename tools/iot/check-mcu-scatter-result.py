#!/usr/bin/env python3
"""Exercise actual installed sender with consumed no-response transport messages."""
import argparse
import ast
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path)
a=p.parse_args()
here=Path(__file__).resolve().parent
# Share the established SDK sender type/macro fixture, not a sender model.
tree=ast.parse((here/'prepare-mcu-sender-check.py').read_text())
prefix=next(ast.literal_eval(n.value) for n in tree.body
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets))
prefix=prefix.replace('int wr_iot_checked,','int wr_iot_sequence_uncertain; int wr_iot_checked,')
start=prefix.index('static int AndesDequeueAndKickOutCmdMsgs(')
end=prefix.index('\n}',start)+2
prefix=prefix[:start]+'''static int transport_result;
static int AndesDequeueAndKickOutCmdMsgs(PRTMP_ADAPTER ad){
 assert(ad==adapter && !freed && pending);
 /* Consume the message: the sender must not inspect it after return. */
 freed=1; current=NULL;
 return transport_result;
}
'''+prefix[end:]
source=(a.candidate/'mcu/andes_core.c').read_text()
start=source.index('static INT32 wr_iot_mcu_send_body(')
end=source.index('\n}',start)+2
body=source[start:end]
tail='''
int main(void){
 struct adapter ad={0}; struct cmd_msg msg;
 ad.flags=ad.MCUCtrl.flags=1; adapter=&ad;
 for(int i=0;i<3;i++){
  transport_result=(int[]){0,1,-1}[i];
  memset(&msg,0,sizeof(msg)); current=&msg; freed=waits=0; pending=0;
  int result=wr_iot_mcu_send_body(&ad,&msg);
  assert(result==transport_result && freed && !waits && !current);
 }
 puts("PASS actual no-response sender propagates success, private refusal and post-publication refusal without consumed-message access; transport injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-scatter-result-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check'
 c.write_text('#include "mcu-boot-result.h"\n'+prefix+body+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function',
                 '-fsanitize=address,undefined','-fno-pie','-no-pie',
                 '-I'+str(a.candidate/'include'),str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)

# Exercise the actual dequeue path, with only PCI/queue operations injected.
base=next(ast.literal_eval(n.value) for n in tree.body
          if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets))
base=base.replace('int wr_iot_checked,','int wr_iot_sequence_uncertain; int wr_iot_checked,')
start=base.index('static int AndesDequeueAndKickOutCmdMsgs(')
end=base.index('\n}',start)+2
base=base[:start]+base[end:]
start=base.index('static int kick_for_precondition(')
end=base.index('\n}',start)+2
base=base[:start]+'''static int kick_for_precondition(PRTMP_ADAPTER ad,struct cmd_msg *msg){
 assert(ad==adapter&&msg==current&&!freed);
 if(mode==1)return NDIS_STATUS_FAILURE; /* Private refusal. */
 if(mode==2)return -1; /* Already ring-owned. */
 freed=1; current=NULL;return 0; /* Transport consumed successfully. */
}
'''+base[end:]
base+='''
static struct cmd_msg *AndesDequeueCmdMsg(struct MCU_CTRL *ctl,int *queue){
 assert(ctl==&adapter->MCUCtrl&&queue==&ctl->txq);
 if(!pending)return NULL;
 pending=0;
 if(mode==3)adapter->flags=fRTMP_ADAPTER_NIC_NOT_EXIST;
 return current;
}
static unsigned AndesGetCmdMsgSeq(PRTMP_ADAPTER ad,struct cmd_msg *msg){
 assert(ad==adapter&&msg==current);return 7;
}
static void AndesBhSchedule(PRTMP_ADAPTER ad){assert(ad==adapter);}
'''
start=source.index('static INT32 AndesDequeueAndKickOutCmdMsgs(')
end=source.index('\n}',start)+2
dispatch=source[start:end]
actual_tail='''
int main(void){
 struct adapter ad;struct cmd_msg msg;
 for(mode=0;mode<4;mode++){
  memset(&ad,0,sizeof(ad));ad.flags=ad.MCUCtrl.flags=1;adapter=&ad;
  ad.chipOps.pci_kick_out_cmd_msg=kick_for_precondition;
  memset(&msg,0,sizeof(msg));current=&msg;
  pending=freed=force_frees=normal_frees=waits=0;
  int result=wr_iot_mcu_send_body(&ad,&msg);
  int expected[4]={0,1,-1,1};
  assert(result==expected[mode]&&!waits);
  assert(force_frees==((mode==1||mode==3)?1:0));
  assert(!normal_frees);
  if(mode==2)assert(!freed&&current==&msg);
  else assert(freed);
 }
 puts("PASS actual dispatcher + no-response sender: success, private refusal, ring-owned refusal, admission closure; PCI operations injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-scatter-dispatch-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check'
 c.write_text('#include "mcu-boot-result.h"\n'+base+dispatch+body+actual_tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function',
                 '-fsanitize=address,undefined','-fno-pie','-no-pie',
                 '-I'+str(a.candidate/'include'),str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
