#!/usr/bin/env python3
"""Actual normal-OFF quarantine adapter with injected firewall and observations."""
from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
source=(here/'quarantine-apply.inc').read_text()
start=source.index('int wr_iot_quarantine_reapply(void)\n{')
end=source.index('\nstatic int wr_iot_policy_current_wan',start)
body=source[start:end]
prefix=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
#if defined(USE_IPV6)
static int gate,network,eligible=1,ready=1,calls,drift;
static int nvram_match(const char *key,const char *value){
 assert(!strcmp(value,"0"));
 if(!strcmp(key,"wr_iot_network_t"))return network==0;
 assert(!strcmp(key,"wr_iot_firewall_t"));return gate==0;
}
static int wr_iot_quarantine_can_reapply(void){return eligible;}
static int wr_iot_quarantine_ready(void){return ready;}
static void start_firewall_ex(void){calls++;if(drift==1)gate=1;if(drift==2)network=1;}
#endif
'''
tail=r'''
int main(void){
#if defined(USE_IPV6)
 assert(wr_iot_quarantine_reapply()&&calls==1);
 gate=1;assert(!wr_iot_quarantine_reapply()&&calls==1);gate=0;
 network=1;assert(!wr_iot_quarantine_reapply()&&calls==1);network=0;
 eligible=0;assert(!wr_iot_quarantine_reapply()&&calls==1);eligible=1;
 ready=0;assert(!wr_iot_quarantine_reapply()&&calls==2);ready=1;
 drift=1;assert(!wr_iot_quarantine_reapply()&&calls==3);gate=0;
 drift=2;assert(!wr_iot_quarantine_reapply()&&calls==4);network=0;
 drift=0;assert(wr_iot_quarantine_reapply()&&calls==5);
#else
 assert(!wr_iot_quarantine_reapply());
#endif
 puts("PASS actual normal-OFF quarantine reapply: closed gates/eligibility, post-firewall readiness and gate drift; IPv6 absence refuses; observations injected");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='iot-quarantine-reapply-') as d:
    unit=Path(d)/'check.c';unit.write_text(prefix+body+tail)
    for ipv6 in (False,True):
        binary=Path(d)/('with-ipv6' if ipv6 else 'without-ipv6')
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined','-fno-pie','-no-pie',
                        *(['-DUSE_IPV6'] if ipv6 else []),str(unit),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True)
