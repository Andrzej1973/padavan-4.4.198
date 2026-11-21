"""Execute actual initial terminal cleanup wrapper for RELEASE."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-release.py')}
s=(here/'check-physical-initial-release.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<release fixture>','exec'),ns)
code=ns['code'].replace('#include "physical-initial-main-completion.inc"','#include "physical-initial-main-completion.inc"\n#include "physical-initial-cleanup.inc"',1)
code=code.replace('#include "physical-initial-cleanup.inc"',r'''
static RTMP_ADAPTER *fault_after_drop;
static unsigned wrapper_drops;
static int observed_drop(struct wr_iot_physical_stop_pins *p){
 int result=wr_iot_physical_stop_pins_drop(p);wrapper_drops++;
 if(result&&fault_after_drop)fault_after_drop->wr_iot_physical_lifetime.main_open_token++;
 return result;
}
#define wr_iot_physical_stop_pins_drop observed_drop
#include "physical-initial-cleanup.inc"
#undef wr_iot_physical_stop_pins_drop
''',1)
a=code.index(' struct wr_iot_physical_stop_pins release_local={0};')
b=code.index(' assert(wr_iot_physical_initial_terminal_clear(&released_cache)&&pid_refs==1);',a)
code=code[:a]+r'''
 ad.wr_iot_transition.mt_radio_off_stage=3;
 assert(wr_iot_physical_initial_cleanup(&ad,&main_dev,&release_request,&released_cache)==-EAGAIN);
 assert(!released_cache.ready&&!released_cache.cleanup_phase&&pid_refs==2);
 assert(modules==2&&tasks==2&&devices==2);
 ad.wr_iot_transition.mt_radio_off_stage=4;
 fault_after_drop=&ad;
 assert(wr_iot_physical_initial_cleanup(&ad,&main_dev,&release_request,&released_cache)==-EAGAIN);
 assert(released_cache.cleanup_phase==2&&!released_cache.ready&&wrapper_drops==1);
 assert(modules==1&&tasks==1&&devices==1&&ad.wr_iot_physical_lifetime.active);
 assert(!wr_iot_physical_initial_terminal_reply(&released_cache,&release_request,wire,64));
 assert(wr_iot_physical_initial_cleanup(&ad,&main_dev,&release_request,&released_cache)==-EAGAIN);
 assert(wrapper_drops==1&&released_cache.cleanup_phase==2);
 {struct wr_iot_physical_initial_request bad=release_request;bad.attempt++;
  assert(wr_iot_physical_initial_cleanup(&ad,&main_dev,&bad,&released_cache)==-EBUSY);}
 fault_after_drop=NULL;ad.wr_iot_physical_lifetime.main_open_token--;
 assert(!wr_iot_physical_initial_cleanup(&ad,&main_dev,&release_request,&released_cache));
 assert(released_cache.ready&&released_cache.cleanup_phase==3&&wrapper_drops==1);
 assert(!ad.wr_iot_physical_lifetime.active&&!ad.wr_iot_physical_initial.task);
 assert(modules==1&&tasks==1&&devices==1&&pid_refs==2);
 for(unsigned repeat=0;repeat<3;repeat++){
  assert(!wr_iot_physical_initial_cleanup(&ad,&main_dev,&release_request,&released_cache));
  assert(wr_iot_physical_initial_terminal_reply(&released_cache,&release_request,wire,64));
 }
 assert(modules==1&&tasks==1&&devices==1&&pid_refs==2);
'''+code[b:]

with tempfile.TemporaryDirectory(prefix='wr-initial-release-') as d:
 root=Path(d)
 for p in here.glob('*.h'):
  text=p.read_text()
  if p.name in ('radio-transition.h','radio-transition-api.h'):
   text=text.replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;')
  (root/p.name).write_text(text)
 unit=root/'check.c';unit.write_text(code);binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual initial cleanup wrapper RELEASE: checked stage refusal preserves pins/cache, post-drop identity fault retains phase2/no reply, exact retry no second drop, repeated terminal no extra refs; kernel primitives injected')
