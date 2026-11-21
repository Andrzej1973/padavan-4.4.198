"""INITIAL tri-state entry; selector and physical owner actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include "initial-restart-entry.h"
#include "initial-restart-select.h"
#include "rc-physical-stop.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int owned,entropy_ok=1,zero,selection=1,claim=1,selects,claims,entropy_calls;
int wr_iot_rc_restart_owned(void){return owned;}
static int entropy(void*out,unsigned n,unsigned flags){assert(n==32&&flags==1);entropy_calls++;memset(out,zero?0:7,n);return entropy_ok?32:15;}
#define WR_IOT_GETRANDOM(out,n,flags) entropy(out,n,flags)
enum wr_iot_initial_selection wr_iot_initial_restart_select(const unsigned char*n,struct wr_iot_idle_result*out){assert(n[0]==7);selects++;*out=(struct wr_iot_idle_result){2,3,4};return selection;}
int wr_iot_rc_physical_begin_initial_selected(const struct wr_iot_rc_physical_intent*i,const unsigned char*n,const struct wr_iot_idle_result*s){assert(i->restart==1&&i->radio_on==1&&i->reload==1&&n[0]==7&&s->epoch==2&&s->generation==3&&s->serial==4);claims++;return claim;}
#include "initial-restart-entry.c"
int main(void){
 assert(wr_iot_initial_restart_entry(0,1)==WR_RADIO_ENTRY_NATIVE&&!entropy_calls);
 assert(wr_iot_initial_restart_entry(1,2)==WR_RADIO_ENTRY_REFUSED&&!entropy_calls);
 wr_iot_rc_shutdown.active=1;assert(wr_iot_initial_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!entropy_calls);wr_iot_rc_shutdown.active=0;
 owned=1;assert(wr_iot_initial_restart_entry(1,1)==WR_RADIO_ENTRY_NATIVE&&!entropy_calls);owned=0;
 entropy_ok=0;assert(wr_iot_initial_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!selects&&!claims);entropy_ok=1;
 zero=1;assert(wr_iot_initial_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!selects&&!claims);zero=0;
 selection=0;assert(wr_iot_initial_restart_entry(1,1)==WR_RADIO_ENTRY_NATIVE&&selects==1&&!claims);
 selection=-1;assert(wr_iot_initial_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&selects==2&&!claims);
 selection=1;claim=0;assert(wr_iot_initial_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&claims==1);
 claim=1;assert(wr_iot_initial_restart_entry(1,1)==WR_RADIO_ENTRY_OWNED&&claims==2);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-entry-') as d:
 p=Path(d)/'test.c';p.write_text(body);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=10)
print('PASS INITIAL tri-state entry: existing owned path delegates, failed entropy/proof/claim refuse without legacy fallback, exact selection passed to physical claim; adapters injected, net_wifi unbound')
