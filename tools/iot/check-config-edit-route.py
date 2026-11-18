from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
shared=here.parent/'band-steering'
source_text=(here/'check-save-route.py').read_text()
namespace={'__file__':str(here/'check-save-route.py')}
exec(compile(source_text[:source_text.index('with tempfile.TemporaryDirectory(')],'<actual Save route actors>','exec'),namespace)
body=namespace['body'].split('int main(int argc,char **argv)')[0]
for declaration in (
 'enum wr_iot_result_state wr_iot_rc_config_execute(const struct wr_iot_control_request *r){(void)r;assert(0);return WR_IOT_RESULT_RECOVERY;}\n',
 'enum wr_iot_result_state wr_iot_rc_config_continue(const char *id,unsigned long long t){(void)id;(void)t;assert(0);return WR_IOT_RESULT_RECOVERY;}\n',
 'int wr_iot_rc_config_terminal_ready(const struct wr_iot_control_result *r){(void)r;assert(0);return 0;}\n'):
 assert body.count(declaration)==1
 body=body.replace(declaration,'',1)
body=body.replace('return wr_iot_rc_save_observed(r);','return wr_iot_rc_edit_observed(r);')
body+=r'''
#include "config-edit-server.h"
#include "http-edit-request.h"
static unsigned long long edit_now=10;
static unsigned char entropy_counter=0x5a;
unsigned long long fixture_edit_clock(void){return edit_now;}
int fixture_edit_entropy(void *context,unsigned char *bytes,unsigned int length)
{assert(!context&&length==32);memset(bytes,entropy_counter++,length);return 32;}
int main(int argc,char **argv)
{
 struct sigaction action={0};struct wr_iot_config_view view;
 struct wr_iot_control_request request={0};struct wr_iot_control_result result;
 struct wr_iot_mailbox mailbox;char revision[33],new_revision[33],file[PATH_MAX];
 int mode=argc>1?atoi(argv[1]):0,before,index;
 (void)id;(void)drain;
 m=mmap(NULL,sizeof(*m),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);assert(m!=MAP_FAILED);
 action.sa_handler=reaper;sigemptyset(&action.sa_mask);assert(!sigaction(SIGCHLD,&action,NULL));reset();
 wr_iot_rc_shutdown.active=0;m->allow=1;m->manual=mode==2;m->unknown=mode==4;
 m->present=mode!=6;assert(wr_iot_saved_config_encode(m->record,sizeof(m->record),&config));
 assert(wr_iot_rc_save_backend_install()&&wr_iot_rc_edit_backend_install());
 assert(!wr_iot_rc_edit_backend_install());
 assert(wr_iot_rc_edit_view(30,&view,revision)&&view.key_present==(mode!=6)&&!view.enabled);
 if(mode==7)assert(wr_iot_rc_edit_view(30,&view,new_revision));
 memset(request.id,"abcdef01"[mode],32);request.created=wr_iot_control_now();
 request.edit.mode=mode==0||mode==6||mode==7?WR_IOT_EDIT_RAM:mode==2?WR_IOT_EDIT_AUTO:WR_IOT_EDIT_EXPLICIT;
 request.operation=WR_IOT_OPERATION_CONFIG_EDIT_RAM+request.edit.mode;
 memcpy(request.edit.id,request.id,33);request.edit.created=request.created;
 memcpy(request.edit.revision,revision,33);request.edit.action=mode==6?WR_IOT_CONFIG_KEY_REPLACE:WR_IOT_CONFIG_KEY_KEEP;
 request.edit.fields=config;strcpy(request.edit.fields.profile.ssid,"Edited IoT");
 if(mode==6)strcpy(request.edit.fields.profile.password,"replacement-key");
 else memset(request.edit.fields.profile.password,0,sizeof(request.edit.fields.profile.password));
 /* Feed the actual HTTP form parser into the actual client/queue/RC path.
  * The server supplies mode; neither body identity nor caller transaction
  * fields may acquire ownership. Authentication itself remains an SDK actor. */
 struct wr_iot_config_edit_record parsed={0},untouched;
 char form[1024],csrf[33];memset(csrf,'9',32);csrf[32]=0;
 int length=snprintf(form,sizeof(form),
  "wr_iot_request_enable=0&wr_iot_request_ssid=Edited+IoT&wr_iot_request_psk=%s&"
  "wr_iot_request_gateway=%s&wr_iot_request_mask=%s&wr_iot_request_start=%s&"
  "wr_iot_request_end=%s&token=%s&revision=%s&key_action=%s",
  mode==6?"replacement-key":"",config.profile.gateway,config.profile.mask,
  config.profile.first,config.profile.last,csrf,revision,mode==6?"replace":"keep");
 assert(length>0&&(size_t)length<sizeof(form));
 memset(&parsed,0x5a,sizeof(parsed));untouched=parsed;
 assert(!wr_iot_http_edit_request_read(&parsed,0,"POST","application/x-www-form-urlencoded",csrf,form,(size_t)length,request.edit.mode));
 assert(!memcmp(&parsed,&untouched,sizeof(parsed))&&!m->writes&&!m->commits&&!wr_iot_rc_pending());
 assert(!wr_iot_http_edit_request_read(&parsed,1,"GET","application/x-www-form-urlencoded",csrf,form,(size_t)length,request.edit.mode));
 csrf[0]='8';
 assert(!wr_iot_http_edit_request_read(&parsed,1,"POST","application/x-www-form-urlencoded",csrf,form,(size_t)length,request.edit.mode));
 assert(!memcmp(&parsed,&untouched,sizeof(parsed))&&!m->writes&&!m->commits);
 csrf[0]='9';
 assert(wr_iot_http_edit_request_read(&parsed,1,"POST","application/x-www-form-urlencoded",csrf,form,(size_t)length,request.edit.mode));
 assert(!parsed.id[0]&&!parsed.created&&parsed.mode==request.edit.mode&&parsed.action==request.edit.action);
 assert(parsed.fields.profile.enabled==request.edit.fields.profile.enabled&&!strcmp(parsed.revision,revision));
#define SAME_FIELD(field) assert(!strcmp(parsed.fields.profile.field,request.edit.fields.profile.field))
 SAME_FIELD(ssid);SAME_FIELD(password);SAME_FIELD(gateway);SAME_FIELD(mask);SAME_FIELD(first);SAME_FIELD(last);
#undef SAME_FIELD
 if(mode==3)strcpy(m->record,"foreign");
 if(mode==5)edit_now=40;
 wr_iot_mailbox_init(&mailbox);
 assert(wr_iot_rc_submit_edit(&parsed.fields,parsed.revision,parsed.mode,parsed.action,request.id));
 wr_iot_saved_wipe(&parsed,sizeof(parsed));wr_iot_saved_wipe(form,sizeof(form));
 before=reaped;
 assert(wr_iot_rc_dispatch());
 if(mode==7){
  assert(!wr_iot_rc_pending()&&!m->writes&&!m->commits);
  assert(wr_iot_mailbox_open(&mailbox,WR_IOT_CONTROL_DIRECTORY,0)&&wr_iot_mailbox_result(&mailbox,&result));
  assert(result.state==WR_IOT_RESULT_REJECTED);wr_iot_mailbox_close(&mailbox);
  memset(request.id,'2',32);memcpy(request.edit.id,request.id,33);memcpy(request.edit.revision,new_revision,33);
  assert(wr_iot_mailbox_open(&mailbox,WR_IOT_CONTROL_DIRECTORY,0)&&wr_iot_mailbox_submit(&mailbox,&request));
  wr_iot_mailbox_close(&mailbox);assert(wr_iot_rc_dispatch());mode=0;
 }
 if(mode==3||mode==5){
  assert(!wr_iot_rc_pending()&&!wr_iot_rc_shutdown.active&&!m->writes&&!m->commits);
 }else{
  assert(wr_iot_rc_pending());
  assert(!wr_iot_rc_edit_view(30,&view,revision));
  for(index=0;index<1000&&wr_iot_rc_pending();index++){
   assert(wr_iot_rc_continue());
   if(mode==4&&m->commits&&reaped>before)break;
   usleep(5000);
  }
  if(mode==1||mode==4)wait_reap(before);
  assert(m->writes==1&&m->commits==((mode==1||mode==4)?1:0));
  {
   struct wr_iot_saved_config stored={0};
   assert(wr_iot_saved_config_decode(&stored,m->record,strlen(m->record)));
   assert(!strcmp(stored.profile.password,mode==6?"replacement-key":"password123")&&!strcmp(stored.profile.ssid,"Edited IoT"));
  }
 }
 assert(wr_iot_mailbox_open(&mailbox,WR_IOT_CONTROL_DIRECTORY,0)&&wr_iot_mailbox_result(&mailbox,&result));
 wr_iot_mailbox_close(&mailbox);
 if(mode==4){
  assert(result.state==WR_IOT_RESULT_RECOVERY&&wr_iot_rc_pending()&&wr_iot_rc_shutdown.active);
  for(index=0;index<10;index++)assert(wr_iot_rc_continue()&&m->writes==1&&m->commits==1);
 }else{
  assert(!wr_iot_rc_pending()&&!wr_iot_rc_shutdown.active);
  assert(result.state==(mode==3||mode==5?WR_IOT_RESULT_REJECTED:mode==1?WR_IOT_RESULT_SAVED_FLASH:WR_IOT_RESULT_STORED_RAM));
  assert(!wr_iot_rc_continue());
  if(mode!=3&&mode!=5){
   assert(wr_iot_rc_status(request.id,&result));
   strcpy(m->record,"foreign");assert(!wr_iot_rc_status(request.id,&result));
  }
 }
 snprintf(file,sizeof(file),"%s/request",WR_IOT_CONTROL_DIRECTORY);if(!access(file,F_OK))assert(!unlink(file));
 snprintf(file,sizeof(file),"%s/result",WR_IOT_CONTROL_DIRECTORY);assert(!unlink(file));
 snprintf(file,sizeof(file),"%s/lock",WR_IOT_CONTROL_DIRECTORY);assert(!unlink(file));assert(!rmdir(WR_IOT_CONTROL_DIRECTORY));
 munmap((void*)m,sizeof(*m));return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-edit-route-') as directory:
 root=Path(directory);source=root/'check.c';binary=root/'check'
 source.write_text('#include <stdlib.h>\n#include "config-edit-server.h"\n'+body)
 (root/'rc.h').write_text('int nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n')
 (root/'wr-band-settings-snapshot.h').write_bytes((shared/'settings-snapshot.h').read_bytes())
 units=('control-client','control-mailbox','control-server','config-edit-server','config-server','config-save-server','config-save-owner','config-owner','saved-config-store','flash-worker','flash-save-attempt','service-guard')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',
  '-DWR_IOT_NATIVE_FLASH_READBACK_PREPARED=1','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1',
  '-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20',
  '-DWR_IOT_EDIT_CLOCK=fixture_edit_clock','-DWR_IOT_EDIT_ENTROPY=fixture_edit_entropy',
  '-DWR_IOT_SERVICE_LOCK_PATH="'+str(root/'service.lock')+'"','-DWR_IOT_CONTROL_DIRECTORY="'+str(root/'queue')+'"',
  '-DWR_IOT_NOTIFY()=((void)0)','-I'+str(root),'-I'+str(here),str(source),
  *[str(here/(unit+'.c')) for unit in units],str(shared/'settings-snapshot.c'),'-o',str(binary)],check=True)
 for mode in range(8):subprocess.run([str(binary),str(mode)],check=True,timeout=25)
print('PASS actual HTTP edit parser/view/lease/pin/client/queue/RC/RAM/Save/worker composition: auth/CSRF refusal, decoded fields, KEEP/REPLACE, manual RAM, flash, stale/expired rejection and unknown no-replay; native flash/SDK/clock/entropy actors, no HTTP server/device acceptance')
