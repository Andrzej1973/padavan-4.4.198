#!/usr/bin/env python3
"""Execute generated RC physical-stop preflight, without real network calls."""
import ast,subprocess,tempfile
from pathlib import Path
# Extract generator's exact literal installed in net_wifi.c, not a mirrored helper.
tree=ast.parse(Path(__file__).with_name('prepare-rc.py').read_text())
values=[n.value.value for n in tree.body if isinstance(n,ast.Assign) and
 any(isinstance(t,ast.Name) and t.id=='helper' for t in n.targets) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) and 'wr_iot_quiesce(void)' in n.value.value]
assert len(values)==1
source=values[0]
start=source.index('static int wr_iot_quiesce(void)');body=source[start:source.index('\n}',start)+2]
pre=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
static int owned,answer,calls;
static const char *network,*profile,*firewall;
static int wr_iot_bridge_is_owned(void){return owned;}
static int nvram_match(const char *name,const char *value){
 const char *state=0;
 if(!strcmp(name,"wr_iot_network_t"))state=network;
 else if(!strcmp(name,"wr_iot_profile_t"))state=profile;
 else {assert(!strcmp(name,"wr_iot_firewall_t"));state=firewall;}
 return !strcmp(state,value);
}
static int wr_iot_activation_prepare_radio_stop(void){calls++;return answer;}
'''
post=r'''
int main(void){
 const char *values[]={"","0","1","invalid"};
 for(int o=0;o<2;o++)for(int n=0;n<4;n++)for(int p=0;p<4;p++)for(int f=0;f<4;f++)for(int a=-1;a<=2;a++){
  int scope=o||n>1||p>1||f>1;
  owned=o;network=values[n];profile=values[p];firewall=values[f];answer=a;calls=0;
  assert(wr_iot_quiesce()==(!scope||a==1));
  assert(calls==scope);
 }
 puts("PASS actual RC stop preflight: 512 independent gate/ownership cases, empty/zero/invalid settings, exact controller result, no independent network cleanup; backend still unbound");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-radio-stop-') as d:
 src=Path(d)/'t.c';exe=Path(d)/'t';src.write_text(pre+body+post)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
