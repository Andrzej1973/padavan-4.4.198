from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include "radio-off-owner.h"
#include "rc-physical-stop.h"
static int admit=1,terminal,begins,takes;
static struct wr_iot_radio_off_owner *current;
int wr_iot_rc_physical_begin_quiesce(const struct wr_iot_rc_physical_intent*i,const struct wr_iot_control_request*r){
 assert(!i->restart&&!i->radio_on&&!i->reload&&!r->request.enabled);
 assert(current->busy&&!wr_iot_radio_off_begin(current,r));begins++;return admit;
}
int wr_iot_rc_physical_take_off(const char*id,unsigned long long created){
 assert(!strcmp(id,"11111111111111111111111111111111")&&created==7);
 assert(current->busy&&!wr_iot_radio_off_poll(current)&&!wr_iot_radio_off_take(current));takes++;return terminal;
}
int wr_iot_rc_radio_off_policy(int reload,struct wr_iot_radio_off_policy*p){(void)reload;(void)p;assert(0);return 0;}
#include "radio-off-owner.c"
int main(void){
 struct wr_iot_radio_off_owner s={0};current=&s;
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=7};
 assert(!wr_iot_radio_off_poll(&s)&&!wr_iot_radio_off_take(&s));
 admit=0;assert(!wr_iot_radio_off_begin(&s,&off)&&!s.owner&&!s.busy);admit=1;
 off.request.enabled=1;assert(!wr_iot_radio_off_begin(&s,&off));off.request.enabled=0;
 for(int result=-1;result<=1;result+=2){
  terminal=0;assert(wr_iot_radio_off_begin(&s,&off));
  assert(!wr_iot_radio_off_begin(&s,&off)&&!wr_iot_radio_off_take(&s));
  assert(!wr_iot_radio_off_poll(&s));
  s.owner++;assert(!wr_iot_radio_off_poll(&s)&&!wr_iot_radio_off_take(&s));s.owner--;
  terminal=result;assert(wr_iot_radio_off_poll(&s)==result);int before=takes;
  assert(wr_iot_radio_off_poll(&s)==result&&takes==before);
  assert(!wr_iot_radio_off_begin(&s,&off));
  assert(wr_iot_radio_off_take(&s)==result&&!s.owner&&!s.created&&!s.id[0]);
  assert(!wr_iot_radio_off_take(&s));
 }
 assert(begins==3);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-owner-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS OFF consumer: claim once, refusal balanced, pending/foreign/reentrant refusal, exact envelope poll, terminal cached/no replay, one acknowledgement; physical actor injected, RC binding pending')
