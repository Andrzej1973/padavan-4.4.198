#!/usr/bin/env python3
"""Exercise the installed firewall helper; kernel observations are injected."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
s = (a.source / 'trunk/user/rc/firewall_ex.c').read_text()
start = s.index('static int wr_iot_firewall_quarantine(')
opening = s.index('{', start)
depth, end = 1, opening + 1
while depth:
    depth += (s[end] == '{') - (s[end] == '}')
    end += 1
body = s[start:end]
start = s.index('static int wr_iot_nat_policy(')
opening = s.index('{', start)
depth, end = 1, opening + 1
while depth:
    depth += (s[end] == '{') - (s[end] == '}')
    end += 1
body += '\n' + s[start:end]
anchor='int wr_iot_quarantine_apply(void)\n{'
if s.count(anchor)!=1:raise SystemExit('Installed quarantine apply missing or duplicated')
start=s.index(anchor);opening=s.index('{',start);depth=1;end=opening+1
while depth:
    depth+=(s[end]=='{')-(s[end]=='}');end+=1
body+='\n'+s[start:end]
prefix = r'''
#define _GNU_SOURCE
#define USE_IPV6 1
#include "firewall.h"
#include "route-snapshot.h"
#include "dns-config.h"
#include <assert.h>
static int owned=1,gate=1,network=1,ap,inventory_ok=1,route_ok=1,overlap;
static int dns_ok=1,dhcp4=1;static unsigned int dns_port=53,dhcp_port=67,index_value=3;
static const char *gateway="192.168.50.1";
static int wr_iot_bridge_is_owned(void){return owned;}
static int get_ap_mode(void){return ap;}
static int nvram_get_int(const char *key){if(!strcmp(key,"wr_iot_firewall_t"))return gate;assert(!strcmp(key,"wr_iot_network_t"));return network;}
static int apply_allowed=1,apply_ready=1,apply_calls,apply_changed,apply_invalid;
static int nvram_match(const char *key,const char *value){assert(!strcmp(value,"0"));return !apply_invalid&&nvram_get_int(key)==0;}
static int wr_iot_quarantine_can_apply(void){return apply_allowed;}
static void start_firewall_ex(void){apply_calls++;if(apply_changed)gate=1;}
static int wr_iot_quarantine_ready(void){assert(apply_calls);return apply_ready;}
static const char *nvram_safe_get(const char *key){
 if(!strcmp(key,"wr_iot_gateway_t"))return gateway;
 if(!strcmp(key,"wr_iot_mask_t"))return "255.255.255.0";
 if(!strcmp(key,"wr_iot_start_t"))return "192.168.50.20";
 assert(!strcmp(key,"wr_iot_end_t"));return "192.168.50.200";
}
static unsigned int fixture_index(const char *name){assert(!strcmp(name,"br-iot"));return index_value;}
static int fixture_services(const char *path,unsigned int *dns,int *dhcp,unsigned int *port){assert(!strcmp(path,"/etc/dnsmasq.conf"));*dns=dns_port;*dhcp=dhcp4;*port=dhcp_port;return dns_ok;}
static int fixture_inventory(struct wr_iot_inventory *out,int ignore){assert(ignore==1);memset(out,0,sizeof(*out));out->ranges[0].first=0xc0a80100;out->ranges[0].last=0xc0a801ff;out->count=1;return inventory_ok;}
static int fixture_routes(struct wr_iot_inventory *out,unsigned int index,uint32_t net,uint32_t mask){assert(index==3&&net==0xc0a83200&&mask==0xffffff00);if(overlap){out->ranges[1].first=net;out->ranges[1].last=net|255;out->count=2;}return route_ok;}
#define IFNAME_BR "br0"
static int wr_iot_network_check(const char *g,const char *mask,const char *first,const char *last){assert(g&&mask&&first&&last);return inventory_ok&&route_ok&&!overlap&&index_value!=0;}
#define if_nametoindex fixture_index
#define wr_iot_dns_config_services_at fixture_services
#define wr_iot_inventory_interfaces fixture_inventory
#define wr_iot_route_snapshot_owned fixture_routes
'''
tail = r'''
static void check(int allow,const char *wan,int expected){
 char text[16384];size_t n;FILE *fp=tmpfile();assert(fp);
 assert(wr_iot_firewall_quarantine(fp,allow,"br0",wan));assert(!fflush(fp));rewind(fp);
 n=fread(text,1,sizeof(text)-1,fp);assert(!ferror(fp));text[n]=0;assert(!fclose(fp));
 if(expected==0){assert(!n);return;}
 assert(strstr(text,"-A INPUT -i br-iot -j DROP"));
 if(expected==1){assert(!strstr(text,"-j ACCEPT"));assert(strstr(text,"-A FORWARD -o ra2 -j DROP"));}
 else {assert(strstr(text,"--dport 53 -j ACCEPT"));assert(strstr(text,"--dport 67 -j ACCEPT"));assert(strstr(text,"--dst-range 192.168.1.0-192.168.1.255 -j DROP"));assert(!strstr(text,"--dport 22"));}
}
static void check_nat(const char *wan,int expected){
 char text[1024];size_t n;FILE *fp=tmpfile();assert(fp);
 assert(wr_iot_nat_policy(fp,wan));assert(!fflush(fp));rewind(fp);
 n=fread(text,1,sizeof(text)-1,fp);assert(!ferror(fp));text[n]=0;assert(!fclose(fp));
 if(!expected){assert(!n);return;}
 assert(!strcmp(text,"-A POSTROUTING -s 192.168.50.0/255.255.255.0 -o eth2.2 -j MASQUERADE\n"));
}
int main(void){
 check_nat("eth2.2",1);
 owned=0;check_nat("eth2.2",0);owned=1;gate=0;check_nat("eth2.2",0);gate=1;
 network=0;check_nat("eth2.2",0);network=1;ap=1;check_nat("eth2.2",0);ap=0;
 dns_port=5353;check_nat("eth2.2",0);dns_port=53;dhcp_port=1067;check_nat("eth2.2",0);dhcp_port=67;
 dhcp4=0;check_nat("eth2.2",0);dhcp4=1;dns_ok=0;check_nat("eth2.2",0);dns_ok=1;
 inventory_ok=0;check_nat("eth2.2",0);inventory_ok=1;route_ok=0;check_nat("eth2.2",0);route_ok=1;
 overlap=1;check_nat("eth2.2",0);overlap=0;gateway="invalid";check_nat("eth2.2",0);gateway="192.168.50.1";
 check_nat("",0);check_nat("br0",0);check_nat("br-iot",0);check_nat("eth2.2\n-j ACCEPT",0);check_nat("eth2.2",1);
 owned=0;check(1,"eth2.2",0);owned=1;check(0,"eth2.2",1);check(1,"eth2.2",2);
 gate=0;check(1,"eth2.2",1);gate=1;network=0;check(1,"eth2.2",1);network=1;
 ap=1;check(1,"eth2.2",1);ap=0;dns_ok=0;check(1,"eth2.2",1);dns_ok=1;
 dns_port=0;check(1,"eth2.2",1);dns_port=5353;check(1,"eth2.2",1);dns_port=53;
 dhcp4=0;check(1,"eth2.2",1);dhcp4=1;dhcp_port=1067;check(1,"eth2.2",1);dhcp_port=67;
 index_value=0;check(1,"eth2.2",1);index_value=3;inventory_ok=0;check(1,"eth2.2",1);inventory_ok=1;
 route_ok=0;check(1,"eth2.2",1);route_ok=1;overlap=1;check(1,"eth2.2",1);overlap=0;
 gateway="invalid";check(1,"eth2.2",1);gateway="192.168.50.1";check(1,"eth2.2\n-j ACCEPT",1);
 check(1,"",2);check(1,"eth2.2",2);
 gate=network=0;assert(wr_iot_quarantine_apply());assert(apply_calls==1);
 gate=1;assert(!wr_iot_quarantine_apply());assert(apply_calls==1);gate=0;
 network=1;assert(!wr_iot_quarantine_apply());assert(apply_calls==1);network=0;
 apply_allowed=0;assert(!wr_iot_quarantine_apply());assert(apply_calls==1);apply_allowed=1;
 apply_invalid=1;assert(!wr_iot_quarantine_apply());assert(apply_calls==1);apply_invalid=0;
 apply_ready=0;assert(!wr_iot_quarantine_apply());assert(apply_calls==2);apply_ready=1;
 apply_changed=1;assert(!wr_iot_quarantine_apply());assert(apply_calls==3&&gate==1);
 apply_changed=0;gate=0;assert(wr_iot_quarantine_apply());assert(apply_calls==4);
 puts("PASS installed quarantine apply: disabled gates and eligible bridge required, final policy failure and post-script gate change rejected; firewall execution injected");
 puts("PASS installed IoT firewall and scoped NAT helpers: scoped allow, ownership/gates, DNS/DHCP ports, inventory failures and overlap quarantine; kernel observations injected");return 0;
}
'''
a.output.write_text(prefix + body + '\n' + tail)
