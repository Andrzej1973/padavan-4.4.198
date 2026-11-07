#!/usr/bin/env python3
"""Run extracted host checks against one composed peer candidate, not target firmware."""
import argparse
import hashlib
import json
import subprocess
import sys
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
p.add_argument('--cc',default='gcc')
p.add_argument('--close-predecessor',type=Path,help='stage52 tree for shared close fixture; default sibling peer-legacy-close')
p.add_argument('--only',nargs='+',help='run only named checks; report remains explicitly partial')
a=p.parse_args();candidate=a.candidate.resolve(strict=True);out=a.output.resolve()
if out.exists():p.error('new results directory required')
out.mkdir(parents=True);here=Path(__file__).resolve().parent
specs=[
 ('wds-close','prepare-wds-close-wrapper-check.py',[[]]),
 ('wds-remove-witness','prepare-wds-remove-check.py',[[]]),
 ('address-layout','prepare-wtbl-address-layout-check.py',[[]]),
 ('peer-ready','prepare-peer-ready-publication-check.py',[[]]),
 ('hardware-delete','prepare-wcid-delete-check.py',[[],['-DRTMP_PCI_SUPPORT','-DMT_PS']]),
 ('hardware-update','prepare-wcid-update-check.py',[[],['-DRTMP_PCI_SUPPORT'],['-DMT_PS'],['-DRTMP_PCI_SUPPORT','-DMT_PS']]),
 ('hardware-preflight','prepare-wcid-preflight-check.py',[[]]),
 ('hardware-timeout','prepare-wcid-timeout-check.py',[[],['-DRTMP_PCI_SUPPORT']]),
 ('deletion-admission','prepare-uapsd-delete-join-check.py',[[],['-DUAPSD_SUPPORT']]),
 ('eosp','prepare-uapsd-eosp-release-check.py',[[]]),
 ('uapsd','prepare-wcid-uapsd-check.py',[[]]),
 ('reset','prepare-wcid-reset-writer-check.py',[[],['-DDATA_QUEUE_RESERVE']]),
 ('dequeue','prepare-wcid-dequeue-check.py',[[],['-DMAX_CONTINUOUS_TX_CNT','-DDATA_QUEUE_RESERVE','-DMT_PS']]),
]
retained_wds='Retained; callback join/reaper not bound.' in (candidate/'ap/ap_wds.c').read_text()
if any(sig in (candidate/'mgmt/mgmt_entrytb.c').read_text() for sig in
       ['static BOOLEAN wr_iot_mac_delete_entry(','static BOOLEAN wr_iot_mac_delete_entry_body(']):
 specs.append(('wds-delete-resume','prepare-wds-delete-resume-check.py',[[]]))
timer_fence='BOOLEAN wr_iot_retiring;' in (candidate/'include/rtmp_timer.h').read_text()
if timer_fence:
 specs.extend([('timer-scheduling-fence','prepare-timer-fence-check.py',[[]]),
               ('timer-dispatch-fence','prepare-timer-dispatch-fence-check.py',[[],['-DRTMP_TIMER_TASK_SUPPORT']])])
if retained_wds:
 # The historical freed-pointer witness is inapplicable to retained removal.
 # Check actual parent failure propagation instead; this is not a child reaper test.
 specs=[('child-remove-propagation','prepare-child-remove-propagation-check.py',v)
        if n=='wds-remove-witness' else (n,s,v) for n,s,v in specs]
if (candidate/'include/wr-iot-peer-failed-delete-gate.inc').exists():
 specs.append(('failed-peer-reset-refusal','prepare-peer-failed-delete-check.py',
               [[],['-DRTMP_MAC_PCI']]))
if 'BOOLEAN MacTableReset(' in (candidate/'include/rtmp.h').read_text():
 specs.append(('reset-direct-callers','prepare-peer-reset-callers-check.py',
               [[],['-DDOT11W_PMF_SUPPORT']]))
if 'BOOLEAN APStop(' in (candidate/'include/ap.h').read_text():
 specs.append(('ap-stop-direct-callers','prepare-ap-stop-result-check.py',[[]]))
if 'BOOLEAN APShutdown(' in (candidate/'include/ap.h').read_text():
 specs.extend([
  ('ap-shutdown','prepare-ap-shutdown-result-check.py',
   [[],['-DRTMP_MAC_PCI'],['-DRTMP_MAC_PCI','-DWDS_SUPPORT','-DIGMP_SNOOP_SUPPORT','-DDOT11V_WNM_SUPPORT'],
    ['-DWDS_SUPPORT','-DIGMP_SNOOP_SUPPORT','-DDOT11V_WNM_SUPPORT']]),
  ('shutdown-checked-close','prepare-checked-close-check.py',[[]]),
  ('shutdown-close-chain','prepare-close-chain-check.py',[[]]),
  ('shutdown-mbss-last-close','prepare-mbss-last-close-check.py',[[]]),
 ])
if 'INT RTMPDrvClose(' in (candidate/'include/rt_os_net.h').read_text():
 specs.append(('legacy-close-result','prepare-legacy-close-result-check.py',
               [[],['-DTEST_ABL'],['-DWIFI_DIAG'],['-DTEST_ABL','-DWIFI_DIAG'],
                ['-DTEST_ABL','-DWIFI_DIAG','-DCONFIG_RA_HW_NAT_WIFI_NEW_ARCH']]))
if (candidate/'include/wr-iot-wds-table-transaction.inc').exists():
 for check in ['peer-table-owner','peer-table-reset-owner','peer-open-owner',
               'peer-open-dispatch','peer-startup-insertion','wds-startup-transaction',
               'wds-configured-interface-open','wds-table-transaction']:
  specs.append((check,'check-'+check+'.c',[[]]))
 specs.extend([('wds-configured-loops','prepare-wds-startup-loop-check.py',[[]]),
               ('open-core-dispatch','prepare-peer-open-dispatch-check.py',[[]]),
               ('wds-owned-open','prepare-aux-open-wrapper-check.py',[[]])])
if (candidate/'include/wr-iot-peer-open-client.inc').exists():
 specs.append(('main-open-table-claim','prepare-main-open-table-claim-check.py',[[]]))
if (candidate/'include/wr-iot-peer-close-executor.inc').exists():
 specs.extend([('peer-close-table','check-peer-close-table.c',[[]]),
               ('peer-close-executor','check-peer-close-executor.c',[[]]),
               ('shared-close-bodies','prepare-peer-close-executor-check.py',[[]])])
if 'WR_PEER_CLOSE_RESET' in (candidate/'include/wr-iot-reset-admission.inc').read_text():
 specs.append(('shared-reset-executor','prepare-peer-reset-executor-check.py',[[]]))
if (candidate/'include/wr-iot-peer-normal-insert.inc').exists():
 specs.append(('peer-normal-insert','check-peer-normal-insert.c',[[]]))
if (candidate/'include/wr-iot-peer-normal-delete.inc').exists():
 if 'wr_iot_peer_delete_active' in (candidate/'include/wr-iot-peer-normal-delete.inc').read_text():
  specs.append(('peer-delete-resume-contract','check-peer-delete-resume-contract.c',[[],['-DTEST_DELETE_EXECUTION_LEASE']]))
 else:specs.append(('peer-normal-delete','check-peer-normal-delete.c',[[]]))
if 'BOOLEAN (*RTMPFreeAdapter)(VOID *pAd);' in (candidate/'include/rt_os_net.h').read_text():
 specs.append(('adapter-free-result','prepare-adapter-free-result-check.py',[[],['-DTEST_ABL']]))
if (candidate/'include/wr-iot-peer-adapter-release.inc').exists():
 specs.append(('peer-adapter-release','check-peer-adapter-release.c',[[],['-DWSC_INCLUDED']]))
if 'wr_iot_pci_retirement_work_joined(' in (candidate/'os/linux/pci_main_dev.c').read_text():
 specs.append(('pci-first-work-receipt','prepare-pci-first-work-receipt-check.py',[[]]))
if (candidate/'include/wr-iot-pci-child-snapshot.inc').exists():
 specs.append(('pci-child-snapshot','check-pci-child-snapshot.c',[[]]))
if 'Private per-device allocation from RtmpOSNetDevCreate.' in (candidate/'os/linux/rt_linux.c').read_text():
 specs.append(('netdev-ops-lifetime','prepare-netdev-ops-lifetime-check.py',[[]]))
nettask_source=(candidate/'os/linux/rt_rbus_pci_drv.c').read_text()
if 'wr_iot_aux_close_count_matches(' in (candidate/'include/aux-close-claim.h').read_text():
 specs.append(('aux-removing-close','check-aux-removing-close.c',[[]]))
if 'unregister does not propagate a failed ndo_stop' in (candidate/'ap/ap_apcli.c').read_text():
 specs.append(('aux-remove-close','prepare-aux-remove-close-check.py',[[]]))
if 'CMD_RTPRIV_IOCTL_APC_CLOSE, 0, dev_p, 0) != NDIS_STATUS_SUCCESS' in (candidate/'ap/ap_apcli_inf.c').read_text():
 specs.append(('aux-family-close-result','prepare-aux-family-close-result-check.py',
               [[],['-DCONFIG_RA_HW_NAT_WIFI_NEW_ARCH']]))
if (candidate/'include/wr-iot-aux-family-close-owned.inc').exists():
 specs.append(('aux-family-close-owned','prepare-aux-family-owned-check.py',
               [[],['-DCONFIG_RA_HW_NAT_WIFI_NEW_ARCH']]))
if 'wr_iot_aux_open_reserve(' in (candidate/'ap/ap_apcli_inf.c').read_text():
 specs.append(('aux-owned-open','prepare-aux-open-wrapper-check.py',[[]]))
if 'WR_IOT_CLAIM_ONLY_UP' in (candidate/'common/cmm_cfg.c').read_text():
 specs.append(('virtual-up-claim-only','prepare-virtual-up-claim-only-check.py',
               [[],['-DCONFIG_AP_SUPPORT']]))
if 'WR_IOT_OWNER_ONLY_DOWN' in (candidate/'common/cmm_cfg.c').read_text():
 specs.append(('virtual-down-owner-only','prepare-virtual-down-owner-only-check.py',[[]]))
 if (candidate/'include/wr-iot-aux-family-close-owned.inc').exists():
  specs.append(('aux-open-close-cycle','prepare-aux-open-close-cycle-check.py',
                [[],['-DCONFIG_RA_HW_NAT_WIFI_NEW_ARCH']]))
if 'INT ApCli_VirtualIF_Close_Retry(' in (candidate/'ap/ap_apcli_inf.c').read_text():
 specs.append(('aux-family-direct-retry','prepare-aux-family-retry-check.py',
               [[],['-DCONFIG_RA_HW_NAT_WIFI_NEW_ARCH']]))
if (here/'aux-family-retry-scheduler.h').exists():
 specs.append(('aux-family-retry-scheduler','check-aux-family-retry-scheduler.c',[[]]))
if (candidate/'include/wr-iot-nettask-schedule.inc').exists():
 specs.append(('nettask-exit-failure','prepare-nettask-exit-result-check.py',[[]]))
 extended=['-DCONFIG_ANDES_SUPPORT','-DMT_MAC','-DCONFIG_ATE',
           '-DUAPSD_SUPPORT','-DCONFIG_AP_SUPPORT','-DDFS_SUPPORT']
 specs.append(('nettask-schedule','prepare-nettask-schedule-check.py',[[],extended]))
 if 'wr_created[20]' in nettask_source:
  specs.append(('nettask-init-failure','prepare-nettask-init-failure-check.py',
                [['-DOS_ABL_FUNC_SUPPORT'],['-DOS_ABL_FUNC_SUPPORT',*extended]]))
if a.only:
 missing=set(a.only)-{name for name,_,_ in specs}
 if missing:p.error('unknown/unavailable checks: '+','.join(sorted(missing)))
 specs=[spec for spec in specs if spec[0] in a.only]
report={'scope':'host extracted control-flow tests; mocked primitives/layout/MMIO',
        'selected_checks':a.only,'full_suite':not bool(a.only),
        'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False,
        'known_open_issues':(['WDS detached allocation retained without completion reaper'] if retained_wds else
                             ['WDS registry retains freed device identity'])+['peer completion/reuse identity not bound'],
        'passed':False,'tests':[]}
if (candidate/'include/wr-iot-peer-hardware-insert-result.inc').exists():
 report['known_open_issues'].append('failed unpublished MT insertion retains timers/counters; cleanup unbound')
if timer_fence:
 report['known_open_issues'].append('timer fence does not join admitted callbacks or exclude old WCID/timer reuse')
if (candidate/'include/wr-iot-wds-table-transaction.inc').exists():
 report['known_open_issues'].extend([
  ('adapter free and remaining peer/radio admission paths do not obey one proven lifetime owner'
   if (candidate/'include/wr-iot-peer-close-executor.inc').exists() else
   'full table clears, outer open admission and adapter free do not obey common owner yet'),
  'failed configured WDS ndo_open retains count/owned record/module pin without recovery binding',
  'WDS configuration/address lifetime against all writers unproved',
 ])
try:
 for name,script,variants in specs:
    source=out/(name+'.c')
    if script.endswith('.c'):
        shutil.copyfile(here/script,source)
    else:
        args=[sys.executable,str(here/script),str(candidate),str(source)]
        if name=='nettask-init-failure':
            base=out/'nettask-init-failure-base.c'
            subprocess.run([sys.executable,str(here/'prepare-nettask-schedule-check.py'),
                            str(candidate),str(base)],check=True)
            args=[sys.executable,str(here/script),str(base),str(source),
                  '--caller-source',str(candidate/'common/rtmp_init_inf.c')]
        if name=='shared-close-bodies':
            predecessor=a.close_predecessor or candidate.parent/'peer-legacy-close'
            args.insert(2,str(predecessor))
        if name=='nettask-exit-failure':
            predecessor=a.close_predecessor or candidate.parent/'peer-legacy-close'
            args.insert(2,str(predecessor))
        if name=='wds-owned-open':args.append('--wds-only')
        subprocess.run(args,check=True)
    for i,flags in enumerate(variants):
        exe=out/(name+str(i)+'.exe')
        subprocess.run([a.cc,'-std=c11','-Wall','-Wextra','-Werror','-O2','-I'+str(candidate/'include'),'-I'+str(here),*flags,str(source),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
        report['tests'].append({'name':name,'flags':flags,'passed':True,
                               'fixture_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                               'known_unsafe_retirement_witness':name=='wds-remove-witness'})
 report['passed']=True
finally:
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASS '+str(len(report['tests']))+' extracted host variants; target/runtime unverified')
