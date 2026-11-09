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
static int answer,calls;
/* These configuration observations must never authorize physical teardown. */
#define wr_iot_bridge_is_owned(...) forbidden_bridge_shortcut
#define nvram_match(...) forbidden_nvram_shortcut
static int wr_iot_activation_prepare_radio_stop(void){calls++;return answer;}
'''
post=r'''
int main(void){
 const int results[]={-117,-1,0,1,2,2147483647};
 for(unsigned int i=0;i<sizeof(results)/sizeof(results[0]);i++){
  answer=results[i];calls=0;
  assert(wr_iot_quiesce()==(answer==1));
  assert(calls==1);
 }
 puts("PASS actual RC stop preflight: controller always required; exact success only; no configuration bypass or independent cleanup; backend still unbound");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-radio-stop-') as d:
 src=Path(d)/'t.c';exe=Path(d)/'t';src.write_text(pre+body+post)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
