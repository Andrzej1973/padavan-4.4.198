"""Actual checked completion -> RELEASE -> durable reply/ref cleanup."""
from pathlib import Path
import runpy,subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'check-physical-stop-main-completion.py'))
cancel=runpy.run_path(str(here/'check-physical-stop-cancel.py'))
pid_context=cancel['context'].split('struct pid {',1)[1].split('#include "physical-stop-cancel.inc"',1)[0]
context=base['context'].replace('int main(void){','struct pid {'+pid_context+'\n#include "physical-stop-release.inc"\nint main(void){')
body=base['body'].replace('struct wr_iot_physical_stop_pins detached={0};','').replace('{RTMP_ADAPTER alternative=ad;','{');anchor='''  ad.wr_iot_transition.epoch++;
  assert(wr_iot_physical_stop_main_complete'''
a=body.index(anchor)
insert=r'''
  {struct wr_iot_physical_stop_request rel=arm,bad;
   unsigned char wire[64];struct wr_iot_physical_stop_response response;
   rel.action=WR_STOP_RELEASE;rel.attempt=attempt;
   bad=rel;bad.open_token++;
   assert(wr_iot_physical_stop_release_owned(&ad,&main_dev,&bad,serial,
     &ad.wr_iot_physical_terminal)==-EAGAIN);
   assert(identity.refs==1&&modules==2&&ad.wr_iot_physical_lifetime.active);
   assert(!wr_iot_physical_stop_release_owned(&ad,&main_dev,&rel,serial,
     &ad.wr_iot_physical_terminal));
   assert(!ad.wr_iot_physical_lifetime.active&&modules==1&&tasks==1&&devices==1);
   assert(ad.wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&identity.refs==2);
   for(unsigned i=0;i<3;i++){
    assert(wr_iot_physical_stop_terminal_reply(&ad.wr_iot_physical_terminal,&rel,wire,64));
    assert(wr_iot_physical_stop_response_decode(&response,wire,64,&rel));
    assert(response.status==WR_STOP_RELEASED&&modules==1&&identity.refs==2);
   }
   assert(wr_iot_physical_stop_terminal_clear(&ad.wr_iot_physical_terminal));
   assert(identity.refs==1);
   return 0;
  }
'''
body=body[:a]+insert+'\n }\n return 1;\n}\n'
early='  {struct wr_iot_physical_stop_request premature=arm;\n   premature.action=WR_STOP_RELEASE;premature.attempt=attempt;\n   assert(wr_iot_physical_stop_release_owned(&ad,&main_dev,&premature,serial,\n     &ad.wr_iot_physical_terminal)==-EAGAIN);\n   assert(identity.refs==1&&modules==2&&ad.wr_iot_physical_lifetime.active);\n  }\n'
needle='  assert(wr_iot_physical_stop_main_complete(&ad,&main_dev,serial)==-EAGAIN);'
body=body.replace(needle,early+needle,1)

with tempfile.TemporaryDirectory(prefix='wr-stop-release-') as d:
 root=Path(d);inc=root/'include';inc.mkdir()
 for p in here.glob('*.h'):shutil.copyfile(p,inc/p.name)
 for n in ('radio-transition.h','radio-transition-api.h'):
  s=(inc/n).read_text().replace('virtual_down_stage,virtual_up_stage;', 'virtual_down_stage,virtual_up_stage,mt_radio_off_stage;');(inc/n).write_text(s)
 c=root/'check.c';c.write_text(base['base']['base']['prefix']+context+body)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(inc),'-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual RELEASE: wrong tuple retains refs, completed Main releases extras then fence, durable typed retries no repeated puts; hardware receipts injected')
