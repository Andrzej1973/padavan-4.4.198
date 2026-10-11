/* WR1200JS SoC 2.4 GHz profile rollback. The activation controller must hold
 * the service guard and quiesce the radio before generation or restoration.
 * Capture BEFORE gen_ralink_config_2g: its first write replaces the baseline.
 * No activation caller is installed by this header alone. */
#ifndef WR_IOT_RADIO_PROFILE_STATE_H
#define WR_IOT_RADIO_PROFILE_STATE_H
#include <sys/types.h>
#include "saved-bundle.h"
#include "service-guard.h"
#ifndef WR_IOT_RADIO_PROFILE_PATH
#define WR_IOT_RADIO_PROFILE_PATH "/etc/Wireless/RT2860/RT2860AP.dat"
#endif
struct wr_iot_radio_profile_state {
 struct wr_iot_saved_bundle files;
 int active,generated,recovering,recovered;
 pid_t owner;
};
static inline int wr_iot_radio_profile_guard(void){
 int fd=wr_iot_service_guard_dup();
 if(fd<0)return 0;
 return close(fd)==0;
}
static inline int wr_iot_radio_profile_owned(struct wr_iot_radio_profile_state *s){
 return s&&s->active&&s->owner==getpid()&&wr_iot_radio_profile_guard();
}
static inline int wr_iot_radio_profile_take(struct wr_iot_radio_profile_state *s){
 const char *paths[]={WR_IOT_RADIO_PROFILE_PATH};
 if(!s||s->active||s->files.count||!wr_iot_radio_profile_guard()||
    !wr_iot_bundle_capture(&s->files,paths,1))return 0;
 s->active=1;s->generated=0;s->recovering=0;s->recovered=0;s->owner=getpid();
 return 1;
}
/* generate returns the actual RC generator convention: zero means success.
 * Record the resulting file even when generation reports a partial failure.
 * Retain the snapshot on every error; caller enters activation recovery. */
static inline int wr_iot_radio_profile_generate(struct wr_iot_radio_profile_state *s,
 int (*generate)(int)){
 int result;
 if(!wr_iot_radio_profile_owned(s)||!generate||s->generated||s->recovering||
    !wr_iot_bundle_write_begin(&s->files,0))return 0;
 result=generate(0);
 if(!wr_iot_bundle_write_end(&s->files,0))return 0;
 if(result||!wr_iot_bundle_seal(&s->files))return 0;
 s->generated=1;return 1;
}
static inline int wr_iot_radio_profile_restore(struct wr_iot_radio_profile_state *s){
 if(!wr_iot_radio_profile_owned(s))return 0;
 s->recovering=1;s->recovered=0;
 /* Failure before generation made no owned file writes. */
 if(!s->files.journalled){
  if(!wr_iot_generated_matches(&s->files.generated[0],s->files.paths[0]))return 0;
 }else if(!wr_iot_bundle_restore(&s->files))return 0;
 s->recovered=1;return 1;
}
/* Successful activation retains the baseline until stop/recovery. Release
 * only after profile restoration and previous radio/service readiness. */
static inline int wr_iot_radio_profile_finish(struct wr_iot_radio_profile_state *s){
 if(!wr_iot_radio_profile_owned(s)||!s->recovering||!s->recovered)return 0;
 wr_iot_bundle_release(&s->files);memset(s,0,sizeof(*s));return 1;
}
#endif
