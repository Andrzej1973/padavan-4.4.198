"""Actual combined transaction provider, no ioctl dispatch or hardware action."""
from pathlib import Path
import runpy,subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'check-physical-stop-release.py'))
context=base['context'].replace('int main(void){', '#include "physical-stop-query.inc"\n#include "physical-stop-terminal-replace.inc"\n#include "physical-stop-cancel.inc"\n#include "physical-stop-handler.inc"\nint main(void){')
context=context.replace('static int modules=1,tasks=1,devices=1;', 'static int modules=1,tasks=1,devices=1,fail_module;').replace('modules++;return 1;', 'if(fail_module)return 0;modules++;return 1;')
body=base['body']
a=body.index(' assert(!wr_iot_physical_stop_arm_admit(')
b=body.index(' {\n  struct wr_iot_radio_ticket ticket',a)
# Replace manual ARM and publication with the real provider and lost reply retry.
body=body[:a]+r'''
 unsigned char transaction_wire[64];struct wr_iot_physical_stop_response decoded;
 fail_module=1;
 assert(wr_iot_physical_stop_handle(&ad,&main_dev,&arm,transaction_wire,64)==-ENOMEM);
 assert(!ad.wr_iot_physical_lifetime.active&&modules==1&&tasks==1&&devices==1);
 fail_module=0;
 assert(!wr_iot_physical_stop_handle(&ad,&main_dev,&arm,transaction_wire,64));
 assert(wr_iot_physical_stop_response_decode(&decoded,transaction_wire,64,&arm));
 attempt=decoded.identity.attempt;serial=ad.wr_iot_physical_lifetime.serial;
 assert(modules==2&&tasks==2&&devices==2);
 assert(!wr_iot_physical_stop_handle(&ad,&main_dev,&arm,transaction_wire,64));
 assert(modules==2&&tasks==2&&devices==2);
'''+body[b:]
body=body.replace(' assert(!wr_iot_physical_stop_main_complete(&ad,&main_dev,serial));',r'''
  {struct wr_iot_physical_stop_request q=arm;
   q.action=WR_STOP_QUERY;q.attempt=attempt;
   assert(!wr_iot_physical_stop_handle(&ad,&main_dev,&q,transaction_wire,64));
   assert(wr_iot_physical_stop_response_decode(&decoded,transaction_wire,64,&q));
   assert(decoded.status==WR_STOP_COMPLETE);
  }
''',1)
body=body.replace('wr_iot_physical_stop_release_owned(&ad,&main_dev,&bad,serial,\n     &ad.wr_iot_physical_terminal)', 'wr_iot_physical_stop_handle(&ad,&main_dev,&bad,transaction_wire,64)')
body=body.replace('wr_iot_physical_stop_release_owned(&ad,&main_dev,&rel,serial,\n     &ad.wr_iot_physical_terminal)', 'wr_iot_physical_stop_handle(&ad,&main_dev,&rel,transaction_wire,64)')
# New provider's terminal short path supplies repeated RELEASE reply directly.
anchor='''    assert(wr_iot_physical_stop_terminal_reply(&ad.wr_iot_physical_terminal,&rel,wire,64));'''
assert anchor in body;body=body.replace(anchor,'''    assert(!wr_iot_physical_stop_handle(&ad,&main_dev,&rel,wire,64));''')
# Variables from the removed manual reference path are intentionally unnecessary.
body=body.replace(',bad;',';',1)
with tempfile.TemporaryDirectory(prefix='wr-stop-handler-') as d:
 root=Path(d);inc=root/'include';inc.mkdir()
 for p in here.glob('*.h'):shutil.copyfile(p,inc/p.name)
 for n in ('radio-transition.h','radio-transition-api.h'):
  s=(inc/n).read_text().replace('virtual_down_stage,virtual_up_stage;', 'virtual_down_stage,virtual_up_stage,mt_radio_off_stage;');(inc/n).write_text(s)
 c=root/'check.c';c.write_text(base['base']['base']['base']['prefix']+context+body)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(inc),'-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual provider: ARM/lost reply no extra refs, QUERY records completed Main only, RELEASE and retry return extras once; ioctl/hardware unverified')
