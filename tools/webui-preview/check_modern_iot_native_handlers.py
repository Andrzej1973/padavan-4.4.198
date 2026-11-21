#!/usr/bin/env python3
"""Generated Modern client consumes actual C HTTP handler JSON; RC is substituted."""
from pathlib import Path
import json,runpy,subprocess,tempfile
here=Path(__file__).resolve().parent;iot=here.parent/'iot'
source=(iot/'check-http-handler.c').read_text().split('int main(void){',1)[0]
source=source.replace('static int edit_calls;', 'static const char *fixture_ssid;\nstatic int edit_calls;',1)
old=''' assert(!strcmp(fields->profile.ssid,"IoT")&&!fields->profile.password[0]&&action==WR_IOT_CONFIG_KEY_KEEP);
 assert(!strcmp(revision,"ffffffffffffffffffffffffffffffff"));'''
assert old in source
source=source.replace(old,''' assert(!fields->profile.password[0]&&action==WR_IOT_CONFIG_KEY_KEEP);
 assert(!strcmp(revision,"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"));''',1)
source=source.replace('0123456789abcdef0123456789abcdef','cccccccccccccccccccccccccccccccc')
source=source.replace("memset(revision,'f',32)","memset(revision,'b',32)",1)
start=source.index('view->key_present=1;view->enabled=0;strcpy(view->ssid,')
end=source.index(';',start+len('view->key_present=1;view->enabled=0;'))+1
source=source[:start]+'view->key_present=1;view->enabled=0;snprintf(view->ssid,sizeof(view->ssid),"%s",fixture_ssid);'+source[end:]
start=source.index('static const char *fixture_ssid;')
end=source.index('static int view_calls',start)
source=source[:start]+'static const char *fixture_ssid;\n'+source[end:]
client=(iot/'control-client.c').read_text()
submit_start=client.index('static int random_id(')
submit_end=client.index('static int wr_iot_submit_request(',submit_start)
edit_start=client.index('int wr_iot_rc_submit_edit(',submit_end)
edit_end=client.index('\nint wr_iot_rc_status(',edit_start)
source+='''\nstatic char mailbox_directory[]="/tmp/modern-iot-mailbox-XXXXXX";
#define WR_IOT_CONTROL_DIRECTORY mailbox_directory
#define WR_IOT_NOTIFY() ((void)0)
#include "control-channel.h"
'''+client[submit_start:submit_end]+client[edit_start:edit_end]+'\n'
main=r'''
int main(int argc,char **argv){
 const char *route;if(argc!=7)return 2;
 route=argv[1];mime=argv[2];fixture_ssid=argv[5];
 snprintf(wr_iot_http_csrf,sizeof(wr_iot_http_csrf),"%s",argv[4]);
 if(!strcmp(route,"/wr_iot_token.cgi"))wr_iot_http_token_output(route,NULL);
 else if(!strncmp(route,"/wr_iot_result.cgi?id=",22)){
  requested_id=strchr(route,'=')+1;
  result_state=!strcmp(argv[6],"runtime")?WR_IOT_RESULT_APPLIED:
   !strcmp(argv[6],"save")?WR_IOT_RESULT_SAVED_FLASH:WR_IOT_RESULT_STORED_RAM;
  wr_iot_http_result_output(route,NULL);
 }else{
  if(!strncmp(route,"/wr_iot_edit_",13))assert(mkdtemp(mailbox_directory));
  input(argv[3],(int)strlen(argv[3]));
  if(!strcmp(route,"/wr_iot_view.cgi"))wr_iot_http_view_output(route,NULL);
  else if(!strcmp(route,"/wr_iot_edit_ram.cgi"))wr_iot_http_edit_ram_output(route,NULL);
  else if(!strcmp(route,"/wr_iot_edit_auto.cgi"))wr_iot_http_edit_auto_output(route,NULL);
  else if(!strcmp(route,"/wr_iot_edit_save.cgi"))wr_iot_http_edit_save_output(route,NULL);
  else if(!strcmp(route,"/wr_iot_edit_runtime.cgi"))wr_iot_http_edit_runtime_output(route,NULL);
  else return 3;
  assert(!wr_iot_http_length&&!wr_iot_http_body[0]);
 }
 if(!strncmp(route,"/wr_iot_edit_",13)){
  struct wr_iot_mailbox mailbox;struct wr_iot_control_request queued={0};
  enum wr_iot_config_edit_mode expected;
  char path[PATH_MAX];
  if(!strcmp(argv[6],"ram"))expected=WR_IOT_EDIT_RAM;
  else if(!strcmp(argv[6],"auto"))expected=WR_IOT_EDIT_AUTO;
  else if(!strcmp(argv[6],"save"))expected=WR_IOT_EDIT_EXPLICIT;
  else if(!strcmp(argv[6],"runtime"))expected=WR_IOT_EDIT_RUNTIME;
  else return 4;
  wr_iot_mailbox_init(&mailbox);
  assert(wr_iot_mailbox_open(&mailbox,mailbox_directory,0));
  assert(wr_iot_mailbox_claim(&mailbox,wr_iot_control_now()+1,&queued));
  assert(queued.operation==WR_IOT_OPERATION_CONFIG_EDIT_RAM+expected&&
   queued.edit.mode==expected&&queued.edit.action==WR_IOT_CONFIG_KEY_KEEP&&
   !strcmp(queued.edit.revision,"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")&&
   !strcmp(queued.edit.fields.profile.ssid,argv[5])&&
   !queued.edit.fields.profile.password[0]&&
   !strcmp(queued.edit.fields.profile.gateway,"192.168.50.1")&&
   !strcmp(queued.edit.fields.profile.mask,"255.255.255.0")&&
   !strcmp(queued.edit.fields.profile.first,"192.168.50.20")&&
   !strcmp(queued.edit.fields.profile.last,"192.168.50.200"));
  assert(wr_iot_mailbox_finish(&mailbox,queued.id,WR_IOT_RESULT_REJECTED,
   wr_iot_control_now()+2));wr_iot_mailbox_close(&mailbox);
  assert(snprintf(path,sizeof(path),"%s/result",mailbox_directory)<(int)sizeof(path));assert(!unlink(path));
  assert(snprintf(path,sizeof(path),"%s/lock",mailbox_directory)<(int)sizeof(path));assert(!unlink(path));
  assert(!rmdir(mailbox_directory));
 }
 puts(reply);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='modern-native-handlers-') as td:
 root=Path(td);c=root/'check.c';exe=root/'check';js=root/'modern-iot.js'
 c.write_text('#define _GNU_SOURCE\n#include <stdlib.h>\n'+source+main);js.write_text(runpy.run_path(str(here/'prepare-modern-iot.py'))['asset']())
 subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(iot),str(c),str(iot/'control-mailbox.c'),'-o',str(exe)],check=True)
 # Actual output handler rejection must reach the client as an error, never
 # an accepted record, when a token or content type is invalid.
 token='a'*32
 for content,body in (('application/json','token='+token),
                      ('application/x-www-form-urlencoded','token='+'b'*32)):
  denied=subprocess.check_output([str(exe),'/wr_iot_view.cgi',content,body,
    token,'IoT','ram'],text=True)
  assert json.loads(denied)=={'error':'invalid_request'}
 subprocess.run(['node',str(here/'check_modern_iot.js'),str(js),str(exe),'--handlers'],check=True)
print('PASS Modern IoT -> native C HTTP handlers -> production control-client and mailbox claim: four edit modes, exact profile/revision/key intent; view/result and RC execution/persistence remain fixture boundaries')
