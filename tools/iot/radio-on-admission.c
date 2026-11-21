#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-admission.h"
#include "radio-off-observe.h"
#include "radio-off-profile.h"
#include "rc-runtime.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
static int on_same_receipt(const struct wr_iot_physical_stop_request *expected)
{
 struct wr_iot_physical_stop_request current={0};unsigned char a[64],b[64];
 return wr_iot_rc_radio_off_receipt(&current)&&
  wr_iot_physical_stop_request_encode(a,sizeof(a),expected)&&
  wr_iot_physical_stop_request_encode(b,sizeof(b),&current)&&!memcmp(a,b,sizeof(a));
}
static int on_profile_current(const struct wr_iot_physical_stop_request *receipt)
{
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 return wr_iot_rc_radio_off_profile_current(receipt);
#else
 (void)receipt;return wr_iot_rc_off_profile_current();
#endif
}
static int on_admission_begin(struct wr_iot_on_admission *s,int reload)
{
 struct wr_iot_rc_mode before={0},after={0};struct wr_iot_physical_stop_request receipt={0};int token;
 if((reload!=0&&reload!=1)||!s||s->owner||s->busy||s->phase!=WR_ON_ADMISSION_IDLE||s->profile.active||s->profile.files.count||
    s->fence.owner||s->fence.level||s->guard||wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned)return 0;
 s->busy=1;token=wr_iot_service_guard_enter(1);if(token!=1){s->busy=0;return 0;}
 if(!wr_iot_rc_radio_off_receipt(&receipt)||receipt.action!=WR_STOP_RELEASE||
    !wr_iot_physical_stop_request_valid(&receipt)||!wr_iot_rc_radio_on_mode_read(&before)||
    before.router!=1||before.radio!=1||before.mode!=0||
    !wr_iot_radio_stop_fence_begin(&s->fence)){
  s->busy=0;wr_iot_service_guard_leave(token);return 0;
 }
 s->owner=getpid();s->guard=token;s->released=receipt;s->phase=WR_ON_ADMISSION_REFUSED;
 wr_iot_rc_shutdown.radio_off_owned=1;
 if(on_same_receipt(&s->released)&&wr_iot_radio_resume_down_observed(&s->released)&&
    (reload||on_profile_current(&s->released))&&wr_iot_radio_profile_take(&s->profile)&&
    s->profile.files.saved[0].existed&&s->profile.files.saved[0].size&&
    wr_iot_rc_radio_on_mode_read(&after)&&before.router==after.router&&before.radio==after.radio&&before.mode==after.mode&&
    on_same_receipt(&s->released)&&wr_iot_radio_resume_down_observed(&s->released)&&
    (reload||on_profile_current(&s->released))&&s->profile.files.count==1&&
    wr_iot_generated_matches(&s->profile.files.generated[0],s->profile.files.paths[0])&&
    !wr_iot_rc_shutdown.pending)s->phase=WR_ON_ADMISSION_CAPTURED;
 s->busy=0;return 1;
}
static void on_cancel_cleanup(void *context)
{
 struct wr_iot_on_admission *s=context;volatile unsigned char *p;size_t n;
 wr_iot_bundle_release(&s->profile.files);
 p=(volatile unsigned char *)&s->profile;n=sizeof(s->profile);while(n--)*p++=0;
 wr_iot_rc_shutdown.radio_off_owned=0;s->phase=WR_ON_ADMISSION_CANCELLED;s->busy=0;
 wr_iot_service_guard_leave(s->guard);s->guard=0;
}
int wr_iot_on_admission_cancel(struct wr_iot_on_admission *s)
{
 if(!s||s->owner!=getpid()||s->busy||s->guard!=1||s->fence.owner!=getpid()||s->fence.level!=1||
    !wr_iot_rc_shutdown.active||!wr_iot_rc_shutdown.radio_off_owned||
    (s->phase!=WR_ON_ADMISSION_CAPTURED&&s->phase!=WR_ON_ADMISSION_REFUSED)||
    (s->profile.active&&(s->profile.owner!=getpid()||s->profile.generated||s->profile.recovering||
     s->profile.removing||s->profile.files.journalled||s->profile.files.dirty||s->profile.files.pending)))return 0;
 s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&s->fence,on_cancel_cleanup,s)){s->busy=0;return 0;}
 return s->phase==WR_ON_ADMISSION_CANCELLED;
}

int wr_iot_on_admission_begin(struct wr_iot_on_admission *s)
{return on_admission_begin(s,0);}
int wr_iot_on_admission_begin_reload(struct wr_iot_on_admission *s,int reload)
{return on_admission_begin(s,reload);}
