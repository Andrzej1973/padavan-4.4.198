from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent;candidate=Path(__file__).resolve().parent/'rc-physical-stop.c'
src=(here/'check-rc-physical-initial.py').read_text();ns={'__file__':str(here/'check-rc-physical-initial.py')};exec(compile(src[:src.index('\nwith tempfile.TemporaryDirectory(')],'<fixture>','exec'),ns)
prefix=ns['code'].split('int main(void)',1)[0].replace('#include "'+str(here/'rc-physical-stop.c')+'"','#include "'+str(candidate)+'"')
prefix=prefix.replace('int wr_iot_rc_radio_on_saved_request(struct wr_iot_request *r){(void)r;assert(0);return 0;}','').replace('void wr_iot_rc_initial_restart_detach_commit(void){assert(0);}','')
actors=ns['ordinary_shutdown_actors']
code=prefix+r'''
static int saved_ok=1,saved_enabled=1,saved_reads;
int wr_iot_rc_radio_on_saved_request(struct wr_iot_request *out){
 assert(depth==1&&wr_iot_rc_shutdown.active&&!calls&&!downs&&!initial_calls);saved_reads++;
 if(!saved_ok)return 0;
 memset(out,0,sizeof(*out));out->enabled=saved_enabled;
 if(saved_enabled){strcpy(out->ssid,"saved IoT");strcpy(out->password,"fixture-secret-only");}
 return 1;
}
int main(int argc,char **argv){
 (void)handler;(void)argv;
 struct wr_iot_rc_physical_intent intent={1,1,1};struct wr_iot_rc_physical_resume observed;
 saved_ok=argc!=2;saved_enabled=argc!=3;
 assert(wr_iot_rc_physical_begin_initial_saved(&intent)&&saved_reads==1&&!downs&&!initial_calls);
 if(!saved_ok){
  assert(physical.finishing==-1&&!physical.initial_saved);
  wr_iot_rc_physical_step();assert(physical.result==-1&&!depth&&!downs&&!initial_calls);
  struct wr_iot_request zero={0};assert(!memcmp(&physical.initial_desired,&zero,sizeof(zero)));return 0;
 }
 assert(physical.initial_saved&&physical.initial_desired.enabled==saved_enabled);
 saved_enabled=!saved_enabled; /* Later actor changes must not replace capture. */
 for(unsigned i=0;i<20&&physical.finishing!=1;i++)wr_iot_rc_physical_step();
 assert(physical.finishing==1&&downs==1&&initial_calls==3);
 assert(wr_iot_rc_physical_resume_read(&observed)&&observed.origin==WR_PHYSICAL_ORIGIN_INITIAL);
 assert(observed.resume_needed==!saved_enabled&&observed.desired.enabled==!saved_enabled&&!observed.physical.action);
 if(observed.desired.enabled)assert(!strcmp(observed.desired.ssid,"saved IoT")&&!strcmp(observed.desired.password,"fixture-secret-only"));
 return 0; /* Capture/handoff snapshot only; generation and reopen not accepted. */
}
'''+actors
with tempfile.TemporaryDirectory(prefix='wr-initial-desired-') as d:
 p=Path(d)/'check.c';p.write_text(code+'\nvoid wr_iot_rc_initial_restart_detach_commit(void){assert(0);}\n')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(candidate.parent/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 for args in [[],['refuse'],['disabled','policy']]:subprocess.run([d+'/check']+args,check=True,timeout=15)
print('PASS candidate actual INITIAL owner saved ON/OFF capture, read refusal before ARM/DOWN with cleanup, exact retained desired after typed RELEASE; restore/reopen not exercised by this capture fixture')
