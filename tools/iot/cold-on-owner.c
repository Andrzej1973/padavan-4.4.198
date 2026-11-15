#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-owner.h"
#include "cold-on-recovery.h"
#include "rc-shutdown-admission.h"
static void cold_owner_wipe(void *p,size_t n)
{volatile unsigned char*b=p;while(n--)*b++=0;}
int wr_iot_cold_owner_begin(struct wr_iot_cold_owner *s,
 const struct wr_iot_control_request *input,int reload)
{
 struct wr_iot_request checked={0};struct wr_iot_control_fields fields;
 unsigned char nonce[16]={0};unsigned i,nonzero=0;int claimed=0;
 if(!s||!input||(reload!=0&&reload!=1)||s->owner||s->busy||s->phase!=WR_COLD_OWNER_IDLE||
    s->admission.owner||s->generation.owner||s->main.owner||s->guest.owner||s->multicast.owner||s->services.owner||
    !input->created||!memchr(input->id,0,sizeof(input->id))||!wr_iot_control_id(input->id)||
    (input->request.enabled!=0&&input->request.enabled!=1))return 0;
#define BOUNDED(f) if(!memchr(input->request.f,0,sizeof(input->request.f)))return 0;
 BOUNDED(ssid) BOUNDED(password) BOUNDED(gateway) BOUNDED(mask) BOUNDED(first) BOUNDED(last)
#undef BOUNDED
 fields.values[0]="1";fields.values[1]=(char*)input->request.ssid;fields.values[2]=(char*)input->request.password;
 fields.values[3]=(char*)input->request.gateway;fields.values[4]=(char*)input->request.mask;
 fields.values[5]=(char*)input->request.first;fields.values[6]=(char*)input->request.last;
 if(input->request.enabled){
  if(!wr_iot_request_read(&checked,wr_iot_control_read,&fields,1,1,0,NULL,0))goto done;
 }else if(input->request.ssid[0]||input->request.password[0]||input->request.gateway[0]||
           input->request.mask[0]||input->request.first[0]||input->request.last[0])goto done;
 for(i=0;i<16;i++){
  unsigned char a=input->id[2*i],b=input->id[2*i+1];
  nonce[i]=(unsigned char)(((a<='9'?a-'0':a-'a'+10)<<4)|(b<='9'?b-'0':b-'a'+10));nonzero|=nonce[i];
 }
 if(!nonzero)goto done;
 s->busy=1;
 if(wr_iot_cold_admission_begin(&s->admission,nonce)){
  s->owner=getpid();s->reload=reload;s->input.request=checked;
  memcpy(s->input.id,input->id,sizeof(s->input.id));s->input.created=input->created;
  s->phase=s->admission.phase==WR_COLD_CAPTURED?WR_COLD_OWNER_ADMITTED:WR_COLD_OWNER_RETAINED;
  if(s->phase==WR_COLD_OWNER_RETAINED)cold_owner_wipe(&s->input.request,sizeof(s->input.request));
  claimed=1;
 }
 s->busy=0;
 done:cold_owner_wipe(&checked,sizeof(checked));cold_owner_wipe(nonce,sizeof(nonce));return claimed;
}
static int cold_owner_owned(struct wr_iot_cold_owner *s)
{
 return s&&s->owner==getpid()&&!s->busy&&wr_iot_rc_shutdown.active&&
  wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_rc_shutdown.radio_on_owned&&
  s->admission.owner==getpid();
}
int wr_iot_cold_owner_step(struct wr_iot_cold_owner *s)
{
 int result=0,generated;
 if(!cold_owner_owned(s)||wr_iot_rc_shutdown.pending)return 0;
 s->busy=1;
 switch(s->phase){
 case WR_COLD_OWNER_ADMITTED:
  if(wr_iot_cold_generation_begin(&s->generation,&s->admission,&s->input.request,s->reload)){
   cold_owner_wipe(&s->input.request,sizeof(s->input.request));s->phase=WR_COLD_OWNER_GENERATE;
  }else{cold_owner_wipe(&s->input.request,sizeof(s->input.request));s->phase=WR_COLD_OWNER_RETAINED;}
  break;
 case WR_COLD_OWNER_GENERATE:
  generated=wr_iot_cold_generation_step(&s->generation);
  if(generated==1)s->phase=WR_COLD_OWNER_MAIN_START;
  else if(generated==-1)s->phase=WR_COLD_OWNER_RESTORED;
  break;
 case WR_COLD_OWNER_MAIN_START:
  (void)wr_iot_cold_main_begin(&s->main,&s->generation);
  s->phase=s->main.owner&&s->main.phase!=WR_COLD_MAIN_NOT_SUBMITTED?WR_COLD_OWNER_MAIN_WAIT:WR_COLD_OWNER_RETAINED;
  break;
 case WR_COLD_OWNER_MAIN_WAIT:
  if(wr_iot_cold_main_lan_step(&s->main))s->phase=WR_COLD_OWNER_GUEST_BEGIN;
  break;
 case WR_COLD_OWNER_GUEST_BEGIN:
  if(wr_iot_cold_guest_begin(&s->guest,&s->main))s->phase=WR_COLD_OWNER_GUEST;
  break;
 case WR_COLD_OWNER_GUEST:
  if(wr_iot_cold_guest_step(&s->guest))s->phase=WR_COLD_OWNER_MC_BEGIN;
  break;
 case WR_COLD_OWNER_MC_BEGIN:
  if(wr_iot_cold_multicast_begin(&s->multicast,&s->main,&s->guest))s->phase=WR_COLD_OWNER_MC;
  break;
 case WR_COLD_OWNER_MC:
  if(wr_iot_cold_multicast_step(&s->multicast))s->phase=WR_COLD_OWNER_SERVICES_BEGIN;
  break;
 case WR_COLD_OWNER_SERVICES_BEGIN:
  if(wr_iot_cold_services_begin(&s->services,&s->guest))s->phase=WR_COLD_OWNER_SERVICES;
  break;
 case WR_COLD_OWNER_SERVICES:
  if(wr_iot_cold_services_step(&s->services))s->phase=WR_COLD_OWNER_PREPARED;
  break;
 case WR_COLD_OWNER_PREPARED:
  result=s->generation.admission==&s->admission&&s->main.generation==&s->generation&&
   s->guest.main==&s->main&&s->services.guest==&s->guest&&
   s->multicast.main==&s->main&&s->multicast.guest==&s->guest&&
   wr_iot_cold_multicast_step(&s->multicast)&&wr_iot_cold_services_step(&s->services);
  break;
 default:break;
 }
 s->busy=0;return result;
}
int wr_iot_cold_owner_recover(struct wr_iot_cold_owner *s)
{
 int result;
 if(!cold_owner_owned(s)||s->generation.admission!=&s->admission||s->generation.main_may_have_started)return 0;
 s->busy=1;result=wr_iot_cold_preup_recover(&s->generation);
 if(result==-1){cold_owner_wipe(&s->input.request,sizeof(s->input.request));s->phase=WR_COLD_OWNER_RESTORED;}
 s->busy=0;return result;
}
