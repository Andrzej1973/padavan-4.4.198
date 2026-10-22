#!/usr/bin/env python3
"""Generate a compile probe for the activation headers as staged by RC prep."""
import argparse
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
rc=a.source/'trunk/user/rc'
for name in ('activation.h','request.h','bridge.h','subnet.h','types.h','network-check.h','radio-profile-state.h','disable-services.h','request-snapshot.h','dns-activation.h'):
    if not (rc/'wr-iot'/name).is_file():
        raise SystemExit('missing staged IoT header: '+name)
if not (rc/'shared-wifi'/'validate.h').is_file():
    raise SystemExit('missing staged shared Wi-Fi validator')
report=json.loads((a.source/'iot-rc-source.json').read_text(encoding='utf-8'))
if not report['disable_services_adapter_installed'] or report['disable_services_controller_bound'] or not report['disable_controller_adapter_installed'] or report['disable_controller_radio_bound']:
    raise SystemExit('Candidate disable service scope changed')
local=Path(__file__).parent
for unit,names in (('disable-services',('disable-services.h','dns-activation.h')),
                   ('disable-controller',('disable-controller.h','bridge.h'))):
    expected=(local/(unit+'.c')).read_text(encoding='utf-8')
    for name in names:
        expected=expected.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
    if (rc/('wr-iot-'+unit+'.c')).read_text(encoding='utf-8')!=expected:
        raise SystemExit('Installed disable adapter differs: '+unit)
    if (rc/'Makefile').read_text(encoding='utf-8').count('wr-iot-'+unit+'.o')!=1:
        raise SystemExit('Disable object missing or duplicated: '+unit)
for name in ('disable-services.h','disable-controller.h','request-snapshot.h','dns-activation.h','radio-profile-state.h','profile.h','profile-scan.h','profile-line.h','profile-list.h'):
    if (rc/'wr-iot'/name).read_bytes()!=(local/name).read_bytes():
        raise SystemExit('Installed disable service header differs: '+name)
service=(rc/'services_ex.c').read_text(encoding='utf-8')
prefix='\n'.join(line for line in service.split('#include "rc.h"',1)[0].splitlines() if line.startswith('#include '))+'\n'
if not prefix.startswith('#include <stdio.h>'):
    raise SystemExit('RC include order changed')
anchor='static int wr_iot_restart_candidate_ready(void)\n{'
if service.count(anchor)!=1:
    raise SystemExit('installed IoT candidate readiness missing or duplicated')
begin=service.index(anchor)
end=service.index('\n}',begin)+2
installed=service[begin:end]
if 'wr_iot_network_services_ready' not in installed:
    raise SystemExit('installed candidate readiness does not use protocol check')
firewall=(rc/'firewall_ex.c').read_text(encoding='utf-8')
anchor='int wr_iot_quarantine_apply(void)\n{'
if firewall.count(anchor)!=1:raise SystemExit('installed quarantine apply missing or duplicated')
begin=firewall.index(anchor);end=firewall.index('\n}',begin)+2
apply=firewall[begin:end]
if 'start_firewall_ex();' not in apply or 'wr_iot_quarantine_ready()' not in apply:
    raise SystemExit('installed quarantine apply does not check final policy')
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(prefix+'''#include "rc.h"
#include "wr-iot/network-check.h"
#include "wr-iot/activation.h"
#include "wr-iot/request.h"
#include "wr-iot/radio-profile-state.h"
#include "wr-iot/quarantine-live.h"
#include "wr-iot/quarantine.h"
#include "wr-iot/disable-services.h"
#include "wr-iot/disable-controller.h"
#ifndef USE_IPV6
#define USE_IPV6
#endif
'''+installed+'\n'+apply+'''
int main(void) {
 struct wr_iot_request request;
 struct wr_iot_activation activation;
 struct wr_iot_radio_profile_state profile;
 struct wr_iot_disable_services stop;
 memset(&request,0,sizeof(request));
 memset(&activation,0,sizeof(activation));
 memset(&profile,0,sizeof(profile));
 memset(&stop,0,sizeof(stop));
 if (wr_iot_radio_profile_take(&profile)) {
  (void)wr_iot_radio_profile_generate(&profile,gen_ralink_config_2g);
  if (wr_iot_radio_profile_restore(&profile))
   (void)wr_iot_radio_profile_finish(&profile);
 }
 if (wr_iot_radio_profile_take(&profile)) {
  if (wr_iot_radio_profile_remove_owned(&profile,"IoT","password"))
   (void)wr_iot_radio_profile_commit_removed(&profile);
 }
 return request.enabled || activation.locked || stop.committed || wr_iot_restart_candidate_ready() || wr_iot_quarantine_live(0) || wr_iot_quarantine_apply();
}
''',encoding='utf-8')
print('Prepared staged RC activation/request header compile probe')
