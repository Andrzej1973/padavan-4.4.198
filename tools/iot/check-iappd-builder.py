"""Compile/execute transformed builder fragments; quarantine ordering proof."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
transform=runpy.run_path(str(here/'prepare-iappd-builder.py'))['transform']
source=''
for name,ret in [('ipt_filter_rules','return 0;'),('ipt_filter_default','return;')]:
 source+='\n'+name+'(FILE *fp)\n{\n#if defined(BOARD_WR1200JS)\n if(!quarantine(fp)){fclose(fp);logmessage("IoT Wi-Fi","Firewall quarantine write failed");'+ret+'}\n#endif\n'+('return 1;' if name.endswith('rules') else '')+'\n}\n'
result=transform(source)
try:transform(result)
except ValueError:pass
else:raise AssertionError('duplicate accepted')
try:transform(source.replace('Firewall quarantine write failed','changed',1))
except ValueError:pass
else:raise AssertionError('missing quarantine accepted')
code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define BOARD_WR1200JS 1
static int quarantine(FILE*f){return fputs("-A INPUT -i br-iot -j DROP\n",f)>=0;}
static void logmessage(const char*a,const char*b){(void)a;(void)b;}
'''+result.replace('\nipt_filter_rules(', '\nint ipt_filter_rules(').replace('\nipt_filter_default(', '\nvoid ipt_filter_default(')+r'''
int main(void){
 for(int variant=0;variant<2;variant++){
  FILE*f=tmpfile();assert(f);if(variant)ipt_filter_default(f);else assert(ipt_filter_rules(f));
  rewind(f);char b[1024]={0};assert(fread(b,1,sizeof(b)-1,f)>0);assert(!fclose(f));
  assert(!strcmp(b,"-A INPUT -i br-iot -j DROP\n-A INPUT -i br0 -p tcp --dport 3517 -j ACCEPT\n-A INPUT -i br0 -p udp --dport 3517 -j ACCEPT\n"));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iapp-builder-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS transformed IPv4 normal/default builder fragments: exact fixed LAN rules after IoT DROP, no ra2/IPv6 scope, missing/duplicate hooks refuse; fixture quarantine, not full SDK/kernel proof')
