#!/usr/bin/env python3
"""Install private restart hook only in paired experimental runtime sources."""
from pathlib import Path
import argparse,json,hashlib
here=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
root=a.source.resolve();rc=root/'trunk/user/rc';report=root/'iot-restart-entry-source.json'
for candidate in (report,rc/'wr-iot/restart-entry.h',rc/'wr-iot-restart-entry.c',rc/'wr-iot/initial-restart-entry.h',rc/'wr-iot-initial-restart-entry.c'):
 if candidate.is_symlink() or not candidate.parent.resolve().is_relative_to(root):raise SystemExit('Refuse symlink/outside output')
for candidate in (root/'iot-iapp-policy-source.json',rc/'wr-iot/restart-iapp-policy.h',rc/'net_wifi.c',rc/'wr-iot-rc-backend.c',rc/'Makefile',rc/'wr-iot/radio-entry-result.h'):
 if candidate.is_symlink() or not candidate.is_file() or not candidate.resolve().is_relative_to(root):raise SystemExit('Refuse missing/symlink/outside input')
if (rc/'wr-iot/radio-entry-result.h').read_bytes()!=(here/'radio-entry-result.h').read_bytes():raise SystemExit('Shared radio entry result header changed')
if report.exists():raise SystemExit('Restart entry already prepared')
m=json.loads((root/'iot-iapp-policy-source.json').read_text())
if m.get('board')!='WR1200JS' or m.get('production_ready') is not False or not m.get('iapp_compile_gate_enabled'):raise SystemExit('Paired experimental WR policy required')
if (rc/'wr-iot/restart-iapp-policy.h').read_text()!='#define WR_IOT_IAPP_POLICY_PREPARED 1\n':raise SystemExit('Prepared policy gate required')
net=(rc/'net_wifi.c').read_text();backend=(rc/'wr-iot-rc-backend.c').read_text();make=(rc/'Makefile').read_text()
for marker in ('static struct wr_iot_activation_owner backend;','static struct wr_iot_rebind_owner rebind;'):
 if backend.count(marker)!=1:raise SystemExit('Exact runtime backend owners required')
signature='void\nrestart_wifi_rt(int radio_on, int need_reload_conf)\n{'
if net.count(signature)!=1 or 'WR_IOT_PRIVATE_RESTART_ENTRY' in net or 'wr_iot_rc_restart_owned' in backend:raise SystemExit('Restart source anchor changed')
fence='if(!wr_iot_radio_stop_fence_begin(&wr_iot_fence)){wr_iot_last_stop_result=0;return;}'
opening=net.index(signature)+len(signature)-1
finish=opening+1;depth=1
while depth and finish<len(net):
 depth+=(net[finish]=='{')-(net[finish]=='}');finish+=1
if depth or net[opening:finish].count(fence)!=1:raise SystemExit('Prepared legacy restart fence required')
anchor='wr-iot-restart-scheduler.o'
if make.count(anchor)!=1:raise SystemExit('Runtime scheduler object required')
header=rc/'wr-iot/restart-entry.h';unit=rc/'wr-iot-restart-entry.c'
if header.exists() or unit.exists() or (rc/'wr-iot/initial-restart-entry.h').exists() or (rc/'wr-iot-initial-restart-entry.c').exists():raise SystemExit('Refuse existing entry source')
includes='#if defined(BOARD_WR1200JS)\n#include "wr-iot/restart-entry.h"\n#include "wr-iot/initial-restart-entry.h"\n#include "wr-iot/restart-iapp-policy.h"\n#endif\n'
body='''
#if defined(BOARD_WR1200JS) && WR_IOT_IAPP_POLICY_PREPARED
 /* WR_IOT_PRIVATE_RESTART_ENTRY: before the legacy physical-call fence.
  * Claimed intent never falls through to combined SDK stop/reopen. */
 if(wr_iot_radio_off_entry(radio_on,need_reload_conf)!=WR_RADIO_ENTRY_NATIVE)return;
 if(wr_iot_radio_on_entry(radio_on,need_reload_conf)!=WR_RADIO_ENTRY_NATIVE)return;
 if(wr_iot_initial_restart_entry(radio_on,need_reload_conf)!=WR_RADIO_ENTRY_NATIVE)return;
 if(wr_iot_restart_entry(radio_on,need_reload_conf)!=WR_RADIO_ENTRY_NATIVE)return;
#endif
'''
net=net.replace(signature,includes+signature+body,1)
backend+='''
/* Only the never-opened path remains eligible for separate legacy admission. */
int wr_iot_rc_restart_owned(void)
{
 return rebind.owner||backend.busy||
  (backend.phase!=WR_IOT_OWNER_IDLE&&backend.phase!=WR_IOT_OWNER_INITIAL_OFF);
}
'''
initial_text=(here/'initial-restart-entry.c').read_text()
for h in here.glob('*.h'):initial_text=initial_text.replace('#include "'+h.name+'"','#include "wr-iot/'+h.name+'"')
text=(here/'restart-entry.c').read_text()
for h in here.glob('*.h'):text=text.replace('#include "'+h.name+'"','#include "wr-iot/'+h.name+'"')
# All source anchors checked before outputs. Candidate discarded on write error.
(rc/'net_wifi.c').write_text(net);(rc/'wr-iot-rc-backend.c').write_text(backend)
(rc/'Makefile').write_text(make.replace(anchor,anchor+' wr-iot-restart-entry.o wr-iot-initial-restart-entry.o',1))
header.write_bytes((here/'restart-entry.h').read_bytes());unit.write_text(text)
(rc/'wr-iot/initial-restart-entry.h').write_bytes((here/'initial-restart-entry.h').read_bytes())
(rc/'wr-iot-initial-restart-entry.c').write_text(initial_text)
report.write_text(json.dumps({'board':'WR1200JS','production_ready':False,'private_restart_hook_bound':True,'owned_restart_refusal_no_fallback':True,'initial_restart_hook_bound':True,'historical_radio_on_hook_bound':True,'cold_radio_on_hook_bound':True,'owned_radio_off_hook_bound':True,'physical_runtime_verified':False,'source_sha256':{'net_wifi.c':hashlib.sha256(net.encode()).hexdigest(),'wr-iot-rc-backend.c':hashlib.sha256(backend.encode()).hexdigest(),'wr-iot-restart-entry.c':hashlib.sha256(text.encode()).hexdigest(),'wr-iot-initial-restart-entry.c':hashlib.sha256(initial_text.encode()).hexdigest(),'Makefile':hashlib.sha256((rc/'Makefile').read_bytes()).hexdigest()}},indent=2)+'\n')
print('PASS experimental private restart hook staged before legacy fence; driver/image/runtime acceptance pending')
