/* Actual profile-state header with injected file journal and removal API. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#define WR_IOT_SAVED_BUNDLE_H
struct wr_iot_generated_file {int generation;};
struct wr_iot_saved_bundle {
 size_t count;int sealed,journalled;unsigned int dirty,pending;
 char paths[1][128];struct wr_iot_generated_file generated[1];
 struct {int existed;unsigned char *data;size_t size;} saved[1];
};
static int generation=1,guard=1,remove_ok=1,remove_calls,end_ok=1;
static unsigned char owned_profile[]="Default\nBssidNum=3\nSSID1=Main\nSSID2=Guest\nSSID3=IoT\nWPAPSK1=main-password\nWPAPSK2=guest-password\nWPAPSK3=password\nAuthMode=WPA2PSK;OPEN;WPA2PSK\nEncrypType=AES;NONE;AES\nWmmCapable=1;1;1\nDLSCapable=0;0;0\nNoForwarding=0;1;1\nHideSSID=0;0;0\nStationKeepAlive=0;0;0\nPreAuth=0;0;0\nIEEE8021X=0;0;0\nFixedTxMode=0;0;0\nHT_MCS=33;33;33\n";
static int wr_iot_generated_matches(const struct wr_iot_generated_file *f,const char *path){assert(path);return f->generation==generation;}
static int wr_iot_generated_capture(struct wr_iot_generated_file *f,const char *path){assert(path);f->generation=generation;return 1;}
static int wr_iot_bundle_capture(struct wr_iot_saved_bundle *s,const char *const *paths,size_t count){
 assert(count==1);s->count=1;strcpy(s->paths[0],paths[0]);s->generated[0].generation=generation;
 s->saved[0].existed=1;s->saved[0].data=owned_profile;s->saved[0].size=sizeof(owned_profile)-1;return 1;
}
static int wr_iot_bundle_write_begin(struct wr_iot_saved_bundle *s,size_t i){
 assert(!i);if(!wr_iot_generated_matches(&s->generated[0],s->paths[0]))return 0;
 s->journalled=1;s->dirty=s->pending=1;return 1;
}
static int wr_iot_bundle_write_end(struct wr_iot_saved_bundle *s,size_t i){
 assert(!i);if(!end_ok)return 0;s->generated[0].generation=generation;s->pending=0;return 1;
}
static int wr_iot_bundle_seal(struct wr_iot_saved_bundle *s){if(s->pending)return 0;s->sealed=1;return 1;}
static int wr_iot_bundle_restore(struct wr_iot_saved_bundle *s){(void)s;assert(0);return 0;}
static void wr_iot_bundle_release(struct wr_iot_saved_bundle *s){memset(s,0,sizeof(*s));}
int wr_iot_service_guard_dup(void){
#ifdef _WIN32
 return guard?open("NUL",O_RDONLY):-1;
#else
 return guard?open("/dev/null",O_RDONLY):-1;
#endif
}
int wr_iot_profile_remove(const char *path,const char *ssid,const char *password){
 assert(path&&!strcmp(ssid,"IoT")&&!strcmp(password,"password"));remove_calls++;
 if(remove_ok)generation++;
 return remove_ok;
}
#include "radio-profile-state.h"
int main(void){
 struct wr_iot_radio_profile_state s={0};
 assert(wr_iot_radio_profile_take(&s));
 assert(wr_iot_radio_profile_can_remove(&s,"IoT","password"));
 assert(!wr_iot_radio_profile_can_remove(&s,"Other","password"));guard=0;
 assert(wr_iot_radio_profile_cancel(&s)&&!s.active);guard=1;
 assert(wr_iot_radio_profile_take(&s));remove_ok=0;
 assert(!wr_iot_radio_profile_remove_owned(&s,"IoT","password"));
 assert(s.active&&s.removing&&!s.generated&&!s.files.journalled&&remove_calls==1);
 assert(!wr_iot_radio_profile_cancel(&s));
 assert(!wr_iot_radio_profile_restore(&s)&&!wr_iot_radio_profile_commit_removed(&s));
 remove_ok=1;assert(wr_iot_radio_profile_remove_owned(&s,"IoT","password"));
 assert(wr_iot_radio_profile_remove_owned(&s,"IoT","password")&&remove_calls==2);
 guard=0;assert(!wr_iot_radio_profile_commit_removed(&s));guard=1;
 assert(wr_iot_radio_profile_commit_removed(&s)&&!s.active);
 assert(wr_iot_radio_profile_take(&s));end_ok=0;
 assert(!wr_iot_radio_profile_remove_owned(&s,"IoT","password")&&s.active&&s.files.pending);
 assert(!wr_iot_radio_profile_remove_owned(&s,"IoT","password")&&remove_calls==3);
 assert(!wr_iot_radio_profile_restore(&s)&&!wr_iot_radio_profile_commit_removed(&s));
 wr_iot_bundle_release(&s.files);memset(&s,0,sizeof(s));end_ok=1;
 assert(wr_iot_radio_profile_take(&s));generation++;
 assert(!wr_iot_radio_profile_remove_owned(&s,"IoT","password")&&remove_calls==3);
 wr_iot_bundle_release(&s.files);
 puts("PASS actual radio profile removal state: current-file ownership, safe retry, no duplicate removal, no old IoT restoration, uncertainty retains snapshot; file operations injected");
 return 0;
}
