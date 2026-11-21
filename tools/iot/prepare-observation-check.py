#!/usr/bin/env python3
"""Extract the active-policy observer; injected reads are not kernel proof."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('quarantine',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
source=a.quarantine.read_text(encoding='utf-8')
anchor='int wr_iot_policy_rules_observed(const char *ipv4,const char *ipv6)'
if source.count(anchor)!=1:
    raise SystemExit('Active policy observation missing or duplicated')
start=source.index(anchor);opening=source.index('{',start);end=opening+1;depth=1
while depth:
    depth+=(source[end]=='{')-(source[end]=='}');end+=1
function=source[start:end]
a.output.write_text('''#include <assert.h>
#include <stdio.h>
#include <string.h>
static int guard=7,close_failed,active=1,v4=1,v6=1,drop_active;
static int reads,observations;
static int wr_iot_service_guard_dup(void){return guard;}
static int close(int fd){assert(fd==guard);return close_failed;}
static int wr_iot_bss_is_active(void){observations++;return active;}
static int wr_iot_policy_live(int ipv6,const char *rules){
 assert(!strcmp(rules,ipv6?"rules6":"rules4"));reads++;
 if(ipv6&&drop_active)active=0;
 return ipv6?v6:v4;
}
'''+function+'''
int main(void){
 assert(wr_iot_policy_rules_observed("rules4","rules6")&&reads==2&&observations==2);
 reads=observations=0;guard=-1;
 assert(!wr_iot_policy_rules_observed("rules4","rules6")&&!reads&&!observations);
 guard=7;close_failed=1;
 assert(!wr_iot_policy_rules_observed("rules4","rules6")&&!reads&&!observations);
 close_failed=0;active=0;
 assert(!wr_iot_policy_rules_observed("rules4","rules6")&&!reads);
 active=1;v4=0;
 assert(!wr_iot_policy_rules_observed("rules4","rules6")&&reads==1);
 reads=0;v4=1;v6=0;
 assert(!wr_iot_policy_rules_observed("rules4","rules6")&&reads==2);
 reads=0;v6=1;drop_active=1;
 assert(!wr_iot_policy_rules_observed("rules4","rules6")&&reads==2&&!active);
 reads=observations=0;
 assert(!wr_iot_policy_rules_observed(NULL,"rules6")&&!reads&&!observations);
 puts("PASS active policy observer: held guard, active BSS before/after, both rule families, refusal on lost observations; reads injected");
 return 0;
}
''',encoding='utf-8')
print('Prepared actual active-policy observation fixture with injected read results')
