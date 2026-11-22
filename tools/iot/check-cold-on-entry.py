"""Actual no-receipt selector/entry with saved request and cold slot actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-cold-on-select.py')}
exec((here/'check-cold-on-select.py').read_text().split('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(void){',1)[0]+r'''
#include <time.h>
#include "control-record.h"
static int entropy_ok=1,clock_ok=1,saved_ok=1,saved_enabled=1,begin_ok=1,cold_owned,begins,saved_reads;
static struct wr_iot_control_request captured;
static int entry_entropy(void*p,unsigned n,unsigned flags){assert(n==32&&flags==1);memset(p,0,n);((unsigned char*)p)[0]=1;return entropy_ok?32:31;}
static int entry_clock(clockid_t id,struct timespec*out){assert(id==CLOCK_MONOTONIC);out->tv_sec=8;out->tv_nsec=0;return clock_ok?0:-1;}
#define WR_IOT_GETRANDOM(b,n,f) entry_entropy(b,n,f)
#define clock_gettime entry_clock
int wr_iot_cold_on_pending(void){return cold_owned;}
int wr_iot_rc_radio_on_saved_request(struct wr_iot_request*r){
 assert(depth==1);saved_reads++;memset(r,0,sizeof(*r));r->enabled=saved_enabled;
 if(saved_enabled){strcpy(r->ssid,"IoT");strcpy(r->password,"iot-password");strcpy(r->gateway,"192.168.30.1");strcpy(r->mask,"255.255.255.0");strcpy(r->first,"192.168.30.10");strcpy(r->last,"192.168.30.40");}
 return saved_ok;
}
int wr_iot_rc_cold_on_begin(const struct wr_iot_control_request*r,int reload){
 assert(!depth&&!history&&!wr_iot_rc_shutdown.active&&reload==1&&r->created==8&&strlen(r->id)==32&&r->request.enabled==saved_enabled);
 begins++;captured=*r;if(begin_ok){cold_owned=1;wr_iot_rc_shutdown.radio_off_owned=1;}return begin_ok;
}
#include "cold-on-entry.c"
#include "rc-physical-stop.h"
int wr_iot_radio_on_off_ready(void){return 0;}
int wr_iot_rc_restart_owned(void){assert(0);return 0;}
int wr_iot_rc_mode_read(struct wr_iot_rc_mode*m){(void)m;assert(0);return 0;}
int wr_iot_rc_physical_begin_quiesce(const struct wr_iot_rc_physical_intent*i,const struct wr_iot_control_request*r){(void)i;(void)r;assert(0);return 0;}
int wr_iot_rc_radio_on_begin(const struct wr_iot_control_request*r,int reload){(void)r;(void)reload;assert(0);return 0;}
int wr_iot_rc_radio_off_begin(const struct wr_iot_control_request*r,int reload){(void)r;(void)reload;assert(0);return 0;}
#include "restart-entry.c"

static void reset(void){
 memset(&wr_iot_rc_shutdown,0,sizeof(wr_iot_rc_shutdown));cold_owned=history=reads=mode_reads=fault=0;
 policy=main_down=bss=guard_ok=mode_ok=saved_ok=begin_ok=clock_ok=entropy_ok=1;bridge=dns=mode=0;router=radio=1;
}
int main(void){
 int old_begins;
 reset();assert(wr_iot_radio_on_entry(0,1)==WR_RADIO_ENTRY_NATIVE&&!begins);
 reset();fault=1;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_NATIVE&&!saved_reads&&!begins&&!depth);
 reset();main_down=0;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_NATIVE&&!saved_reads&&!begins&&!depth);
 reset();fault=3;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!saved_reads&&!begins&&!depth);
 reset();saved_ok=0;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&saved_reads==1&&!begins&&!depth);
 reset();entropy_ok=0;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!reads&&!begins&&!depth);
 reset();clock_ok=0;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!reads&&!begins&&!depth);
 reset();history=1;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!reads&&!begins);
 for(saved_enabled=0;saved_enabled<=1;saved_enabled++){
  reset();old_begins=begins;
  assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_OWNED&&begins==old_begins+1&&cold_owned&&!depth);
  assert(!strcmp(captured.id,"01000000000000000000000000000000"));
  if(saved_enabled)assert(!strcmp(captured.request.password,"iot-password"));else assert(!captured.request.password[0]&&!captured.request.gateway[0]);
  assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&begins==old_begins+1);
 }
 reset();begin_ok=0;old_begins=begins;
 assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&begins==old_begins+1&&!cold_owned&&!depth);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cold-entry-') as d:
 p=Path(d)/'check.c';p.write_text(body);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual cold selector+entry: missing DOWN proof/Main-UP delegates native guard; partial proof refuses, valid ON/OFF saved request copied, root begin outside guard, duplicate refused, no post-eligibility fallback; entropy/time/NVRAM/root actors')
