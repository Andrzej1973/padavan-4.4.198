#!/usr/bin/env python3
"""Read-only observer with actual owner/runner/snapshot/OFF; driver/service hooks injected."""
from pathlib import Path
import ast,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-activation-owner-composition.py').read_text()
body=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets))
prefix=(here/'check-start-closed-rollback-composition.c').read_text().split('int main(void){',1)[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('int wr_iot_open_controller_recovery_read(', 'int wr_iot_close_controller_begin(', 'int wr_iot_close_controller_advance(')))+'\n'
prefix+=(here/'check-driver-close-controller.c').read_text().split('int main(void)',1)[0]
body=body.replace('#include "activation-owner.h"','#include "activation-observe.h"')
body=body.replace('s->phase=WR_IOT_COMMIT_ACTIVE;return 1;','s->owner=getpid();s->open_token=3;s->phase=WR_IOT_COMMIT_ACTIVE;return 1;')
hooks=r'''
static int services_ok=1,filter_ok=1;
static unsigned long long live_token=3,live_epoch=1,live_generation=2;
int wr_iot_network_services_ready(const char *g){assert(depth&&g);return services_ok;}
int wr_iot_active_filter_observed_current(void){assert(depth);return filter_ok;}
int wr_iot_driver_open_current_read(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_open_current_result *r){assert(depth&&a);*r=(struct wr_iot_driver_open_current_result){live_epoch,live_generation,live_token};return 1;}
'''
body=body.replace('int main(void){',hooks+'int main(void){',1)
anchor='  struct wr_iot_control_request off='
pos=body.index(anchor)
body=body[:pos]+r'''
  struct wr_iot_control_result observed={.state=WR_IOT_RESULT_APPLIED,.created=input.created};
  strcpy(observed.id,input.id);
  assert(wr_iot_activation_owner_observed(&owner,&observed)&&!depth);
  struct wr_iot_activation_owner before=owner;int before_writes=writes;
  for(unsigned field=7;field<16;field++){
   char saved[128];strcpy(saved,values[field].value);strcpy(values[field].value,"foreign");
   assert(!wr_iot_activation_owner_observed(&owner,&observed)&&!depth);
   strcpy(values[field].value,saved);
  }
  services_ok=0;assert(!wr_iot_activation_owner_observed(&owner,&observed));services_ok=1;
  filter_ok=0;assert(!wr_iot_activation_owner_observed(&owner,&observed));filter_ok=1;
  bridge_address_ok=0;assert(!wr_iot_activation_owner_observed(&owner,&observed));bridge_address_ok=1;
  live_token=4;assert(!wr_iot_activation_owner_observed(&owner,&observed));live_token=3;
  live_epoch=2;assert(!wr_iot_activation_owner_observed(&owner,&observed));live_epoch=1;
  live_generation=3;assert(!wr_iot_activation_owner_observed(&owner,&observed));live_generation=2;
  rollback_dns=1;assert(!wr_iot_activation_owner_observed(&owner,&observed));rollback_dns=0;
  s.open.owner=0;assert(!wr_iot_activation_owner_observed(&owner,&observed));s.open.owner=getpid();
  s.commit.owner=0;assert(!wr_iot_activation_owner_observed(&owner,&observed));s.commit.owner=getpid();
  assert(!memcmp(&before,&owner,sizeof(owner))&&writes==before_writes&&!depth);
'''+body[pos:]
anchor='  assert(owner.phase==WR_IOT_OWNER_OFF);'
body=body.replace(anchor,anchor+r'''
  assert(!wr_iot_activation_owner_observed(&owner,&observed));
  strcpy(observed.id,off.id);observed.created=off.created;
  assert(wr_iot_activation_owner_observed(&owner,&observed)&&!depth);
  before=owner;before_writes=writes;
  for(unsigned field=7;field<16;field++){
   char saved[128];strcpy(saved,values[field].value);strcpy(values[field].value,"foreign");
   assert(!wr_iot_activation_owner_observed(&owner,&observed)&&!depth);
   strcpy(values[field].value,saved);
  }
  observed_serial++;assert(!wr_iot_activation_owner_observed(&owner,&observed));observed_serial--;
  s.admission.snapshot.active=1;assert(!wr_iot_activation_owner_observed(&owner,&observed));s.admission.snapshot.active=0;
  assert(!memcmp(&before,&owner,sizeof(owner))&&writes==before_writes&&!depth);
''')
body=body.replace('PASS retained activation owner with actual runner/admission/snapshot/normal OFF:', 'PASS read-only activation observation with actual owner/runner/snapshot/normal OFF:')
with tempfile.TemporaryDirectory(prefix='iot-activation-observe-compose-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 units=('activation-observe.c','activation-owner.c','active-stop.c','start-runner.c','start-network-rollback.c','start-close.c','start-closed-rollback.c','precreated-stop.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
