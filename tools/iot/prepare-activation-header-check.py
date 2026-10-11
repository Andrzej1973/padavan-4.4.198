#!/usr/bin/env python3
"""Generate a compile probe for the activation headers as staged by RC prep."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
rc=a.source/'trunk/user/rc'
for name in ('activation.h','request.h','bridge.h','subnet.h','types.h','network-check.h','radio-profile-state.h'):
    if not (rc/'wr-iot'/name).is_file():
        raise SystemExit('missing staged IoT header: '+name)
if not (rc/'shared-wifi'/'validate.h').is_file():
    raise SystemExit('missing staged shared Wi-Fi validator')
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
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(prefix+'''#include "rc.h"
#include "wr-iot/network-check.h"
#include "wr-iot/activation.h"
#include "wr-iot/request.h"
#include "wr-iot/radio-profile-state.h"
#include "wr-iot/quarantine-live.h"
'''+installed+'''
int main(void) {
 struct wr_iot_request request;
 struct wr_iot_activation activation;
 struct wr_iot_radio_profile_state profile;
 memset(&request,0,sizeof(request));
 memset(&activation,0,sizeof(activation));
 memset(&profile,0,sizeof(profile));
 if (wr_iot_radio_profile_take(&profile)) {
  (void)wr_iot_radio_profile_generate(&profile,gen_ralink_config_2g);
  if (wr_iot_radio_profile_restore(&profile))
   (void)wr_iot_radio_profile_finish(&profile);
 }
 return request.enabled || activation.locked || wr_iot_restart_candidate_ready() || wr_iot_quarantine_live(0);
}
''',encoding='utf-8')
print('Prepared staged RC activation/request header compile probe')
