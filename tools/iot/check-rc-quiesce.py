"""Reuse the actual RC/backend/owner fixture with private restart-OFF admission."""
from pathlib import Path
import ast,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-rc-backend-composition.py').read_text()
ns={'__file__':str(here/'check-rc-backend-composition.py')}
exec(compile(source[:source.index('with tempfile.TemporaryDirectory(')],'<actual RC fixture setup>','exec'),ns)
units=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='units' for t in n.targets))
ns['prefix']='static unsigned long long quiesce_read_epoch=1;\n'+ns['prefix']
assert ns['prefix'].count('{1,2,3,observed_serial}')==1
ns['prefix']=ns['prefix'].replace('{1,2,3,observed_serial}','{quiesce_read_epoch,2,3,observed_serial}')
body=ns['body'];a=body.index(' submit(&off);');b=body.index(' char path[PATH_MAX];',a)
body=body[:a]+r'''
 struct wr_iot_rc_quiesce q={0};struct wr_iot_driver_closed_result receipt={0};
 struct wr_iot_request desired=backend.start.input.request;
 off.created=on.created+1;
 assert(!wr_iot_rc_quiesce_begin(&q,&off));
 wr_iot_rc_shutdown.active=1;
 filter_ok=0;assert(!wr_iot_rc_quiesce_begin(&q,&off)&&!q.owner&&!depth);filter_ok=1;
 assert(wr_iot_rc_quiesce_begin(&q,&off)&&q.active&&q.resume_needed);
 assert(!memcmp(&q.desired,&desired,sizeof(desired)));
 assert(!wr_iot_rc_quiesce_begin(&q,&off));
 for(unsigned i=0;i<60&&backend.stop.stop.phase!=WR_IOT_STOP_ISOLATE;i++)
  assert(!wr_iot_rc_quiesce_advance(&q,&receipt));
 assert(backend.stop.stop.phase==WR_IOT_STOP_ISOLATE&&depth==3);
 quarantine_ready=0;
 for(unsigned i=0;i<3;i++)assert(!wr_iot_rc_quiesce_advance(&q,&receipt));
 assert(closes==1&&depth==3&&!receipt.close_serial);
 assert(!raise(SIGTERM)&&!shutdowns&&wr_iot_rc_shutdown.pending==SIGTERM);
 quarantine_ready=1;
 for(unsigned i=0;i<60&&!q.complete;i++)(void)wr_iot_rc_quiesce_advance(&q,&receipt);
 assert(q.complete&&!q.active&&q.resume_needed&&receipt.close_serial&&!depth);
 assert(wr_iot_rc_shutdown.active&&!shutdowns);
 assert(backend.phase==WR_IOT_OWNER_OFF&&!backend.start.input.request.enabled);
 assert(!backend.start.input.request.password[0]);
 assert(!memcmp(&q.desired,&desired,sizeof(desired))); /* Normal OFF wiped runner, not resume intent. */
 quiesce_read_epoch=2;
 assert(!wr_iot_rc_quiesce_advance(&q,&receipt)&&!receipt.adapter_epoch&&!receipt.close_serial);
 assert(q.complete&&q.resume_needed&&!memcmp(&q.desired,&desired,sizeof(desired)));
 quiesce_read_epoch=1;
 observed_serial++;assert(!wr_iot_rc_quiesce_advance(&q,&receipt)&&!receipt.close_serial);observed_serial--;
 assert(wr_iot_rc_quiesce_advance(&q,&receipt));
 q.owner++;assert(!wr_iot_rc_quiesce_advance(&q,&receipt)&&!receipt.close_serial);q.owner--;
 q.created++;assert(!wr_iot_rc_quiesce_advance(&q,&receipt));q.created--;
 int pending=wr_iot_rc_shutdown_end();assert(pending==SIGTERM);assert(!raise(pending)&&!shutdowns&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 struct wr_iot_rc_quiesce already_off={0};wr_iot_rc_shutdown.active=1;
 assert(wr_iot_rc_quiesce_begin(&already_off,&off)&&already_off.complete&&!already_off.resume_needed);
 assert(!already_off.desired.password[0]&&wr_iot_rc_quiesce_advance(&already_off,&receipt));
 assert(!wr_iot_rc_shutdown_end()&&!depth);

'''+body[b:]
body=body.replace('ON and OFF published APPLIED','ON published APPLIED; private OFF completed').replace('pending SIGTERM delivered only after terminal publication','pending SIGTERM retained through OFF and routed to normal physical cleanup')
prepared_body=body.replace('#include "rc-backend.c"','#include "rc-backend.c"\n#include "rc-profile-history.inc"')
prepared_body=prepared_body.replace('#include "rc-profile-history.inc"',
 'int wr_iot_restart_profile_file_current(const struct wr_iot_request *r){(void)r;return 0;}\n#include "rc-profile-history.inc"')

prepared_body=prepared_body.replace('int main(void){','int main(int argc,char **argv){assert(argc==2);')
anchor=' struct wr_iot_rc_quiesce q={0};struct wr_iot_driver_closed_result receipt={0};'
assert prepared_body.count(anchor)==1
prepared_body=prepared_body.replace(anchor,r'''
 FILE *profile=fopen(argv[1],"w");assert(profile&&fputs("verified fixture profile A\n",profile)>=0&&!fclose(profile));
 struct wr_iot_profile_binding b={.kind=WR_PROFILE_BACKEND_ACTIVE};
 struct wr_iot_restart_profile_receipt file={.owner=getpid(),.valid=1};
 memcpy(b.id,backend.start.input.id,sizeof(b.id));b.created=backend.start.input.created;
 b.identity=backend.start.open.attempt.identity;assert(strlen(argv[1])<sizeof(file.path));strcpy(file.path,argv[1]);
 assert(wr_iot_generated_capture(&file.file,file.path));
 {int g=wr_iot_service_guard_enter(1);assert(wr_iot_rc_profile_history_remember(&b,&file));wr_iot_service_guard_leave(g);}
'''+anchor)
anchor=' assert(!memcmp(&q.desired,&desired,sizeof(desired)));'
assert anchor in prepared_body
prepared_body=prepared_body.replace(anchor,anchor+r'''
 assert(q.profile_receipt.valid&&q.profile_binding.created==b.created&&
  !strcmp(q.profile_binding.id,b.id)&&q.profile_binding.identity.adapter_epoch==b.identity.adapter_epoch);
''')
anchor=' assert(!wr_iot_rc_shutdown_end()&&!depth);'
assert prepared_body.count(anchor)==1
prepared_body=prepared_body.replace(anchor,anchor+'\n assert(!unlink(argv[1]));')

with tempfile.TemporaryDirectory(prefix='wr-rc-quiesce-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';binary=Path(d)/'check'
 for prepared,source in [(0,body),(1,prepared_body)]:
  unit.write_text(ns['prefix']+'\n#include "check-reopen-unused.h"\n'+source)
  subprocess.run(['gcc','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED='+str(prepared),'-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
  subprocess.run([str(binary),str(Path(d)/'profile')],check=True,timeout=15)
print('PASS private restart OFF with actual backend/owner: current ACTIVE required, normal CLOSE once, isolation refusal retained, fresh released CLOSE, desired settings survive runner wipe, foreign/stale contexts refuse; no physical reopen')
