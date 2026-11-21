"""Actual OFF entry -> RC ppoll owner -> terminal receipt publication."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-rc-radio-off-composition.py')}
exec((here/'check-rc-radio-off-composition.py').read_text().rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
code=ns['code']
code='#define _GNU_SOURCE\nstatic int entry_guard;\nstatic int off_entry_entropy(void*,unsigned,unsigned);\n#define WR_IOT_GETRANDOM(b,n,f) off_entry_entropy(b,n,f)\n'+code
code=code.replace('void wr_iot_service_guard_leave(int token){(void)token;assert(0);}', 'void wr_iot_service_guard_leave(int token){assert(token==1&&entry_guard==1);entry_guard=0;}')
code=code.replace('off_transport=physical_pending=1;', 'assert(!entry_guard);off_transport=physical_pending=1;')
code=code.replace('&&t==7','&&t>0')
actors=r'''
#include "restart-entry.c"
enum wr_iot_radio_entry_result wr_iot_cold_on_entry(int on,int reload){(void)on;(void)reload;assert(0);return WR_RADIO_ENTRY_REFUSED;}
static int off_entry_entropy(void*b,unsigned n,unsigned flags){assert(entry_guard&&n==32&&flags==1);memset(b,0x11,n);return 32;}
int wr_iot_service_guard_enter(int on){assert(on==1&&!entry_guard);entry_guard=1;return 1;}
int wr_iot_rc_restart_owned(void){return 1;}
int wr_iot_rc_mode_read(struct wr_iot_rc_mode*m){assert(entry_guard);*m=(struct wr_iot_rc_mode){1,0,0};return 1;}
int wr_iot_rc_radio_on_saved_request(struct wr_iot_request*r){(void)r;assert(0);return 0;}
int wr_iot_rc_radio_on_begin(const struct wr_iot_control_request*r,int reload){(void)r;(void)reload;assert(0);return 0;}
'''
code=code.replace('int main(void){',actors+'\nint main(void){',1)
a='assert(wr_iot_rc_radio_off_begin(&off,1));'
assert code.count(a)==1
code=code.replace(a,'assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_OWNED&&!entry_guard);\n assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_REFUSED);')
a='assert(!wr_iot_rc_radio_off_begin(&off,1));\n pending=resume_pending=0;'
assert code.count(a)==1
code=code.replace(a,'assert(!wr_iot_rc_radio_off_begin(&off,1));\n assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_REFUSED&&!entry_guard);\n pending=resume_pending=0;')
with tempfile.TemporaryDirectory(prefix='wr-off-entry-runtime-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'control-mailbox.c'),str(here/'status-endpoint.c'),str(here/'status-channel.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual OFF entry/RC ppoll/owner: guard handoff, one OFF and terminal receipt, duplicate/receipt refuse, preserved priority and deferred redispatch; physical/SDK followup actors')
