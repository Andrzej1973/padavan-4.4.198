#!/usr/bin/env python3
"""Stage MT7603 IoT CmdQLock adapter lifetime; isolated candidate only."""
import argparse, hashlib, shutil, json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'common/cmm_mac_pci.c': '6a165366afaf461b741809213bbd116b205acddb7aab35109ab3c763ba38d534', 'common/rtmp_init.c': 'cd98dd0d73e5f9a3a57fe7705512b579607929e42436b33cd3ed2f7ed6109cb4', 'os/linux/rt_profile.c': 'f7947cff4fc76f9e14e0dd47d08d653d7189f1766fdc3be0ff1547f82b89a521'}
pins.update({'include/rtmp.h': 'd09360c082a2fac242f84f832f3ed5ac36bd3aaf364f763e1f7733b11a7b1b71', 'common/cmm_cmd.c': '72909114adfad77df4bd038c0ef00d480ae3e5de9b8c0cfafbbda4d73bd5d36d', 'os/linux/pci_main_dev.c': 'a7635ce354c81da36ae17010655796bf191b44b4b485a7278093c1c52f93ddf0'})
pins.update({'os/linux/rt_linux.c': '0a85539938acd21d242ec2f1941fbac0f61f419ff91855ef5798118bee64cbee', 'os/linux/rt_linux_symb.c': '3ea641ca06d0f9b56d6efa11bdb73ea30f53a7bb9986dbdb7e83cfc77c077fe2', 'include/rt_os_util.h': '00ac3a302872fe6dbd6bb05d850616082cfbecc55d26b5d4b102d9844e28fda8'})
pins.update({'os/linux/rt_rbus_pci_drv.c':'b83006235986d79cb4020c310962e275edb10f8d080ed56fe2492f1cfd23dc40'})
parent_path=src.with_name(src.name+'.manifest.json')
parent=json.loads(parent_path.read_text())
if parent.get('production_installed') is not False or parent.get('target_compiled') is not False:
 p.error('unsupported parent acceptance claims')
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=parent['merged_driver_sha256']:p.error('parent driver differs from strict merge manifest')
texts={}
for n,h in pins.items():
 raw=(src/n).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=h:p.error('unreviewed predecessor: '+n)
 texts[n]=raw.decode()
guard='#if defined(MT7603) && defined(DMA_RESET_SUPPORT)\n'
inverse='#if !defined(MT7603) || !defined(DMA_RESET_SUPPORT)\n'
n='common/cmm_mac_pci.c'
for statement in ['NdisAllocateSpinLock(pAd, &pAd->CmdQLock);','NdisFreeSpinLock(&pAd->CmdQLock);']:
 lines=texts[n].splitlines(keepends=True);count=0;new=[]
 for line in lines:
  if statement in line:
   count+=1;new.extend([inverse,line,'#endif\n'])
  else:new.append(line)
 if count!=2:p.error('changed ring CmdQLock inventory')
 texts[n]=''.join(new)
n='common/rtmp_init.c';anchor='\t\tNdisAllocateSpinLock(pAd, &pAd->MgmtRingLock);'
if texts[n].count(anchor)!=1:p.error('adapter lock init changed')
texts[n]=texts[n].replace(anchor,guard+'\t\tNdisAllocateSpinLock(pAd, &pAd->CmdQLock);\n#endif\n'+anchor,1)
n='os/linux/rt_profile.c';anchor='\tNdisFreeSpinLock(&pAd->MgmtRingLock);'
if texts[n].count(anchor)!=1:p.error('adapter lock release changed')
texts[n]=texts[n].replace(anchor,guard+'\tNdisFreeSpinLock(&pAd->CmdQLock);\n#endif\n'+anchor,1)
def one(n,old,new):
 if texts[n].count(old)!=1:p.error('changed admission anchor: '+n)
 texts[n]=texts[n].replace(old,new,1)
one('include/rtmp.h','#include "radio-transition.h"',
    '#include "radio-transition.h"\n#include "terminal-command-owner.h"')
one('include/rtmp.h','\tNDIS_SPIN_LOCK wr_iot_transition_lock;',
    guard+' struct wr_iot_terminal_command_owner wr_iot_terminal_command;\n#endif\n\tNDIS_SPIN_LOCK wr_iot_transition_lock;')
one('common/rtmp_init.c','\t\tNdisAllocateSpinLock(pAd, &pAd->CmdQLock);',
    '        /* One generation for this pinned adapter allocation; never reset on reopen. */\n'
    '        wr_iot_terminal_command_init(&pAd->wr_iot_terminal_command,1UL);\n'
    '\t\tNdisAllocateSpinLock(pAd, &pAd->CmdQLock);')
one('common/cmm_cmd.c','if (pAd->CmdQ.CmdQState & RTMP_TASK_CAN_DO_INSERT)',
    'if ((pAd->CmdQ.CmdQState & RTMP_TASK_CAN_DO_INSERT)\n'+guard+
    '            && wr_iot_terminal_command_enqueue_allowed(&pAd->wr_iot_terminal_command)\n#endif\n        )')
one('os/linux/pci_main_dev.c','\t\tRtmpOSNetDevProtect(0);\n\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);',
    '\t\tRtmpOSNetDevProtect(0);\n'+guard+
    '        RTMP_SPIN_LOCK_IRQSAVE(&adapter->CmdQLock,&flags);\n'
    '        (void)wr_iot_terminal_command_close(&adapter->wr_iot_terminal_command,1UL);\n'
    '        adapter->CmdQ.CmdQState = RTMP_TASK_STAT_STOPED;\n'
    '        RTMP_SPIN_UNLOCK_IRQRESTORE(&adapter->CmdQLock,&flags);\n#endif\n'
    '\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);')
one('include/rt_os_util.h','INT wr_iot_os_timer_task_current(RTMP_OS_TASK *task);',
    'INT wr_iot_os_timer_task_current(RTMP_OS_TASK *task);\nINT wr_iot_os_command_task_current(RTMP_OS_TASK *task);')
one('os/linux/rt_linux.c','#include "wr-iot-timer-os-join.inc"',
    '#include "wr-iot-timer-os-join.inc"\n#include <linux/err.h>\n#include "wr-iot-command-os-join.inc"')
one('os/linux/rt_linux_symb.c','EXPORT_SYMBOL(wr_iot_os_timer_task_current);',
    'EXPORT_SYMBOL(wr_iot_os_timer_task_current);\nEXPORT_SYMBOL(wr_iot_os_command_task_current);')
rbus='os/linux/rt_rbus_pci_drv.c'
one('include/rtmp.h','INT wr_iot_command_task_exit_checked(RTMP_ADAPTER *pAd);',
    'INT wr_iot_command_task_exit_checked(RTMP_ADAPTER *pAd);\n'+guard+
    'INT wr_iot_terminal_command_join_checked(RTMP_ADAPTER *pAd);\n#endif')
one(rbus,'NDIS_STATUS RtmpMgmtTaskInit(RTMP_ADAPTER *pAd)\n{',
    guard+'#include "wr-iot-command-join-shared.inc"\n#include "wr-iot-terminal-command-join.inc"\n#endif\n'
    'NDIS_STATUS RtmpMgmtTaskInit(RTMP_ADAPTER *pAd)\n{\n'+guard+
    ' ULONG wr_flags=0;\n unsigned long wr_attach;\n#endif')
one(rbus,'\tRTMP_OS_TASK_INIT(pTask, "RtmpCmdQTask", pAd);',
    guard+' RTMP_SPIN_LOCK_IRQSAVE(&pAd->CmdQLock,&wr_flags);\n'
    ' wr_attach=pAd->wr_iot_terminal_command.attempt ?\n'
    '  wr_iot_command_attach_begin(&pAd->wr_iot_terminal_command,1UL) :\n'
    '  wr_iot_command_first_attach_begin(&pAd->wr_iot_terminal_command,1UL);\n'
    ' RTMP_SPIN_UNLOCK_IRQRESTORE(&pAd->CmdQLock,&wr_flags);\n'
    ' if(!wr_attach)return NDIS_STATUS_FAILURE;\n#endif\n'
    '\tRTMP_OS_TASK_INIT(pTask, "RtmpCmdQTask", pAd);')
one(rbus,'\tstatus = RtmpOSTaskAttach(pTask, RTPCICmdThread, (ULONG)pTask);',
    '\tstatus = RtmpOSTaskAttach(pTask, RTPCICmdThread, (ULONG)pTask);\n'+guard+
    ' RTMP_SPIN_LOCK_IRQSAVE(&pAd->CmdQLock,&wr_flags);\n'
    ' if(!wr_iot_command_attach_finish(&pAd->wr_iot_terminal_command,1UL,wr_attach))\n'
    '  status=NDIS_STATUS_FAILURE;\n'
    ' RTMP_SPIN_UNLOCK_IRQRESTORE(&pAd->CmdQLock,&wr_flags);\n#endif')
start=texts[rbus].index('INT wr_iot_command_task_exit_checked(')
end=texts[rbus].index('\n}',start)+2
f=texts[rbus][start:end];body=f.index('\n{')+2
f=f[:body]+'\n'+guard+' return wr_iot_command_join_shared_checked(pAd);\n#else'+f[body:-2]+'\n#endif\n}'
texts[rbus]=texts[rbus][:start]+f+texts[rbus][end:]
start=texts[rbus].index('VOID RtmpMgmtTaskExit(');end=texts[rbus].index('\n}',start)+2
f=texts[rbus][start:end];old='\t\tret = RtmpOSTaskKill(&pAd->cmdQTask);'
if f.count(old)!=1:p.error('legacy command kill changed')
f=f.replace(old,guard+'        ret = wr_iot_command_join_shared_checked(pAd);\n#else\n'+old+'\n#endif',1)
texts[rbus]=texts[rbus][:start]+f+texts[rbus][end:]
one('os/linux/pci_main_dev.c',
    '        RTMP_SPIN_UNLOCK_IRQRESTORE(&adapter->CmdQLock,&flags);\n#endif',
    '        RTMP_SPIN_UNLOCK_IRQRESTORE(&adapter->CmdQLock,&flags);\n'
    '        if(wr_iot_terminal_command_join_checked(adapter)!=NDIS_STATUS_SUCCESS)\n'
    '         return; /* No terminal receipt: retain, not adapter-release proof. */\n#endif')

shutil.copytree(src,out)
shutil.copyfile(Path(__file__).with_name('terminal-command-os-join.inc'),out/'include/wr-iot-command-os-join.inc')
shutil.copyfile(Path(__file__).with_name('terminal-command-owner.h'),out/'include/terminal-command-owner.h')
for local,target in [('command-join-shared.inc','wr-iot-command-join-shared.inc'),('terminal-command-join.inc','wr-iot-terminal-command-join.inc')]:
 shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
for n,s in texts.items():(out/n).write_text(s,encoding='utf-8',newline='\n')
actual={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}
report=dict(parent)
report['merged_driver_sha256']=actual
report['candidate_driver_sha256']=dict(parent['candidate_driver_sha256'])
for n,h in actual.items():
 if parent['merged_driver_sha256'].get(n)!=h:report['candidate_driver_sha256'][n]=h
report['terminal_command_layer']={
 'input_manifest_sha256':hashlib.sha256(parent_path.read_bytes()).hexdigest(),
 'preparer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'assets_sha256':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in
 ['terminal-command-owner.h','terminal-command-os-join.inc','command-join-shared.inc','terminal-command-join.inc']},
 'scope':'source binding only; terminal hardware cleanup still unproved'}
report['target_compiled']=False;report['production_installed']=False;report['runtime_verified']=False
out.with_name(out.name+'.manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('Staged CmdQLock allocation before preallocated rings and release with adapter')
