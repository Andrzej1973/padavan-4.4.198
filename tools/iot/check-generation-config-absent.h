/* Legacy cold lifecycle fixture actor; no native snapshot claim. */
#ifndef WR_IOT_CHECK_GENERATION_CONFIG_ABSENT_H
#define WR_IOT_CHECK_GENERATION_CONFIG_ABSENT_H
#include "saved-config-store.h"
int wr_iot_generation_config_capture(struct wr_iot_generation_config *p,
 const char *id,unsigned long long created,struct wr_iot_saved_config *out)
{
 assert(p&&!p->owner&&id&&created&&out);
 p->owner=getpid();p->self=(uintptr_t)p;p->created=created;
 memcpy(p->id,id,sizeof(p->id));return 1;
}
int wr_iot_generation_config_owned(const struct wr_iot_generation_config *p)
{return p&&p->owner==getpid()&&p->self==(uintptr_t)p;}
int wr_iot_generation_config_current(const struct wr_iot_generation_config *p,
 const char *id,unsigned long long created)
{return p&&p->owner==getpid()&&p->self==(uintptr_t)p&&p->created==created&&!strcmp(p->id,id);}
int wr_iot_generation_config_release(struct wr_iot_generation_config *p)
{
 if(!p||p->owner!=getpid()||p->self!=(uintptr_t)p)return 0;
 memset(p,0,sizeof(*p));return 1;
}
int wr_iot_generation_profile_enter(const struct wr_iot_generation_config *p)
{return wr_iot_generation_config_owned(p);}
int wr_iot_generation_profile_leave(const struct wr_iot_generation_config *p)
{return wr_iot_generation_config_owned(p);}
#endif
