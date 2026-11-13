#!/usr/bin/env python3
"""Run actual network sequencer with actual request matcher/gate writer."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-start-network.c').read_text()
for signature in ('int wr_iot_request_network_enable(', 'int wr_iot_request_prepared_matches(', 'int wr_iot_request_stage_matches('):
    start=source.index(signature);end=source.index('\n',start)
    source=source[:start]+source[end+1:]
helpers=r'''
int wr_iot_bridge_is_owned(void){return bridge;}
int wr_iot_bridge_address_matches(const char *g,const char *m){assert(g&&m);return bridge;}
static const char *nvram_safe_get(const char *key){
 if(!strcmp(key,"wr_iot_profile_t"))return "1";
 if(!strcmp(key,"wr_iot_network_t"))return network?"1":"0";
 if(!strcmp(key,"wr_iot_firewall_t"))return policy?"1":"0";
 if(!strcmp(key,"wr_iot_ssid_t"))return "IoT";
 if(!strcmp(key,"wr_iot_psk_t"))return "password123";
 if(!strcmp(key,"wr_iot_gateway_t"))return "192.168.50.1";
 if(!strcmp(key,"wr_iot_mask_t"))return "255.255.255.0";
 if(!strcmp(key,"wr_iot_start_t"))return "192.168.50.20";
 assert(!strcmp(key,"wr_iot_end_t"));return "192.168.50.200";
}
static int nvram_set_int_temp(const char *key,int value){
 assert(!strcmp(key,"wr_iot_network_t")&&value==1&&up&&quarantine&&!policy);
 if(!next(5))return -1;
 network=1;return 0;
}
'''
request=(here/'request-stage.c').read_text()
request=request[request.index('static int wr_iot_request_stage_matches_gates('):]
source=source.replace('#include "start-network.c"',helpers+'\n'+request+'\n#include "start-network.c"')
source=source.replace('struct wr_iot_request request={.enabled=1};','struct wr_iot_request request={.enabled=1,.ssid="IoT",.password="password123",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"};')
source=source.replace('PASS actual pre-OPEN network sequencer:', 'PASS actual network sequencer plus installed matcher/gate writer:')
with tempfile.TemporaryDirectory(prefix='iot-start-network-compose-') as d:
    unit=Path(d)/'check.c';unit.write_text(source);binary=Path(d)/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(unit),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
