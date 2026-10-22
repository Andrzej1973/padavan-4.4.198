/* Actual composition unit with injected profile/service adapters. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define WR_IOT_DISABLE_CONTROLLER_H
struct wr_iot_request_snapshot {int active;char values[9][80];};
struct wr_iot_disable_services {struct wr_iot_request_snapshot settings;int committed;};
struct wr_iot_radio_profile_state {int active,generated;};
struct wr_iot_disable_controller {struct wr_iot_disable_services services;struct wr_iot_radio_profile_state radio;int profile_committed;};
static int fault,bridge=1,down=1,cancels,service_cancels,removes,profile_commits,service_commits,service_attempts;
unsigned int if_nametoindex(const char *name){assert(!strcmp(name,"br-iot"));return bridge;}
int wr_iot_bss_is_down(void){return down;}
static int wr_iot_radio_profile_take(struct wr_iot_radio_profile_state *s){if(fault==1)return 0;s->active=1;return 1;}
static int wr_iot_radio_profile_cancel(struct wr_iot_radio_profile_state *s){assert(s->active&&!s->generated);s->active=0;cancels++;return 1;}
static int wr_iot_disable_services_begin(struct wr_iot_disable_services *s){
 if(fault==2)return 0;
 s->settings.active=1;
 strcpy(s->settings.values[3],"IoT");strcpy(s->settings.values[4],"password");return 1;
}
static int wr_iot_disable_services_cancel(struct wr_iot_disable_services *s){
 assert(s->settings.active&&!s->committed);memset(s,0,sizeof(*s));service_cancels++;return 1;
}
static int wr_iot_radio_profile_can_remove(struct wr_iot_radio_profile_state *s,const char *ssid,const char *password){
 assert(s->active&&!strcmp(ssid,"IoT")&&!strcmp(password,"password"));return fault!=7;
}
static int wr_iot_request_disable_ready(struct wr_iot_request_snapshot *s){assert(s->active);return fault!=8;}
static int wr_iot_disable_services_apply(struct wr_iot_disable_services *s){
 assert(bridge&&down&&s->settings.active);if(fault==3)return 0;
 service_attempts++;
 if(!s->committed)service_commits++;
 s->committed=1;return 1;
}
static int wr_iot_radio_profile_remove_owned(struct wr_iot_radio_profile_state *s,const char *ssid,const char *password){
 assert(s->active&&!bridge&&down&&!strcmp(ssid,"IoT")&&!strcmp(password,"password"));
 if(fault==4)return 0;
 if(!s->generated)removes++;
 s->generated=1;return 1;
}
static int wr_iot_radio_profile_commit_removed(struct wr_iot_radio_profile_state *s){
 if(fault==5||!s->generated)return 0;
 assert(s->active);s->active=0;profile_commits++;return 1;
}
static int wr_iot_disable_services_finish(struct wr_iot_disable_services *s){
 assert(!bridge&&down&&s->committed);if(fault==6)return 0;
 memset(s,0,sizeof(*s));return 1;
}
#include "disable-controller.c"
int main(void){
 struct wr_iot_disable_controller s={0};
 fault=1;assert(!wr_iot_disable_begin(&s)&&!s.radio.active);
 fault=2;assert(!wr_iot_disable_begin(&s)&&!s.radio.active&&cancels==1);
 fault=7;assert(!wr_iot_disable_begin(&s)&&!s.radio.active&&!s.services.settings.active&&cancels==2&&service_cancels==1);
 fault=0;assert(wr_iot_disable_begin(&s)&&s.radio.active&&s.services.settings.active);
 assert(!wr_iot_disable_begin(&s));
 fault=7;assert(!wr_iot_disable_apply_services(&s)&&!service_attempts&&!service_commits);
 fault=3;assert(!wr_iot_disable_apply_services(&s)&&s.radio.active&&!s.services.committed);
 fault=0;assert(wr_iot_disable_apply_services(&s)&&service_commits==1);
 fault=7;assert(!wr_iot_disable_apply_services(&s)&&service_attempts==1&&service_commits==1);fault=0;
 assert(!wr_iot_disable_apply_profile(&s)&&!removes);
 bridge=0;down=0;assert(!wr_iot_disable_apply_profile(&s)&&!removes);
 down=1;assert(!wr_iot_disable_commit(&s)&&!s.profile_committed);
 fault=8;assert(!wr_iot_disable_apply_profile(&s)&&!removes);fault=0;
 fault=4;assert(!wr_iot_disable_apply_profile(&s));fault=0;
 assert(wr_iot_disable_apply_profile(&s)&&removes==1);
 assert(wr_iot_disable_apply_profile(&s)&&removes==1);
 fault=5;assert(!wr_iot_disable_commit(&s)&&s.radio.active);
 fault=6;assert(!wr_iot_disable_commit(&s)&&s.profile_committed&&!s.radio.active&&profile_commits==1);
 assert(!wr_iot_disable_apply_services(&s)&&service_commits==1);
 fault=0;assert(wr_iot_disable_commit(&s)&&profile_commits==1&&!s.services.settings.active&&!s.profile_committed);
 assert(!wr_iot_disable_commit(&s));
 puts("PASS actual normal-OFF composition: read-only capture cancellation, settings/service/profile order, partial commit retry without old-profile restore; adapters injected");
 return 0;
}
