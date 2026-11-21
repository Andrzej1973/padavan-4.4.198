"""Actual adapter QUERY across ARM and changed-epoch Main completion."""
from pathlib import Path
import runpy,subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'check-physical-stop-main-completion.py'))
context=base['context'].replace('int main(void){','#include "physical-stop-response.h"\n#include "physical-stop-query.inc"\nint main(void){')
body=base['body'];anchor=' assert(wr_iot_physical_stop_arm_abort_unpublished(&ad,&main_dev,serial)==-EBUSY);'
# Insert before scenario begins, and before the existing cleanup alternatives.
a=body.index(' {RTMP_ADAPTER alternative=ad;')
early=r'''
 struct wr_iot_physical_stop_request query=arm,bad_query;
 unsigned char query_wire[64];struct wr_iot_physical_stop_response reply;
 query.action=WR_STOP_QUERY;query.attempt=attempt;
 {RTMP_ADAPTER unchanged=ad;
  assert(!wr_iot_physical_stop_query_owned(&ad,&main_dev,&query,serial,query_wire,64));
  assert(!memcmp(&unchanged,&ad,sizeof(ad)));
 }
 assert(wr_iot_physical_stop_response_decode(&reply,query_wire,64,&query));
 assert(reply.status==WR_STOP_ARMED);
 bad_query=query;bad_query.nonce[0]++;
 assert(wr_iot_physical_stop_query_owned(&ad,&main_dev,&bad_query,serial,query_wire,64)==-EAGAIN);
 for(unsigned i=0;i<64;i++)assert(!query_wire[i]);
'''
body=body[:a]+early+body[a:]
anchor='  assert(!wr_iot_physical_stop_main_complete(&ad,&main_dev,serial));'
a=body.index(anchor)
body=body[:a]+r'''
  assert(ad.wr_iot_transition.epoch!=query.epoch);
  assert(!wr_iot_physical_stop_query_owned(&ad,&main_dev,&query,serial,query_wire,64));
  assert(wr_iot_physical_stop_response_decode(&reply,query_wire,64,&query));
  assert(reply.status==WR_STOP_RUNNING);
'''+body[a:]
a=body.index('  ad.wr_iot_peer_table_owner.poisoned=1;')
body=body[:a]+r'''
  assert(!wr_iot_physical_stop_query_owned(&ad,&main_dev,&query,serial,query_wire,64));
  assert(wr_iot_physical_stop_response_decode(&reply,query_wire,64,&query));
  assert(reply.status==WR_STOP_COMPLETE);
  ad.wr_iot_interface_refs[1].generation++;
  assert(wr_iot_physical_stop_query_owned(&ad,&main_dev,&query,serial,query_wire,64)==-EAGAIN);
  ad.wr_iot_interface_refs[1].generation--;
'''+body[a:]
needle='  assert(wr_iot_physical_stop_begin(&ad.wr_iot_physical_stop,attempt,1,2,arm.nonce,current));'
body=body.replace(needle,needle+r'''
  assert(!wr_iot_physical_stop_query_owned(&ad,&main_dev,&query,serial,query_wire,64));
  assert(wr_iot_physical_stop_response_decode(&reply,query_wire,64,&query));
  assert(reply.status==WR_STOP_RUNNING);
''',1)
with tempfile.TemporaryDirectory(prefix='wr-stop-query-') as d:
 root=Path(d);inc=root/'include';inc.mkdir()
 for p in here.glob('*.h'):shutil.copyfile(p,inc/p.name)
 for n in ('radio-transition.h','radio-transition-api.h'):
  s=(inc/n).read_text().replace('virtual_down_stage,virtual_up_stage;', 'virtual_down_stage,virtual_up_stage,mt_radio_off_stage;');(inc/n).write_text(s)
 c=root/'check.c';c.write_text(base['base']['base']['prefix']+context+body)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(inc),'-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual QUERY: ARMED, RUNNING across epoch change, exact COMPLETE, wrong nonce/registration refusal with cleared output; software/kernel fixtures only')
