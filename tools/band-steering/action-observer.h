#ifndef WR_BAND_ACTION_OBSERVER_H
#define WR_BAND_ACTION_OBSERVER_H
#include "../connected-devices/action-channel.h"
#include "../connected-devices/steering-action.h"
#include <fcntl.h>
#include <unistd.h>
#define WR_ACTION_ENDPOINT_PATH "/var/run/wr-device-observer/actions"
struct wr_band_action_observer {struct wr_action_channel channel;struct wr_action_reporter reporter;};
static inline int wr_band_action_emit(const struct wr_action_event *e,void *context){
 struct wr_band_action_observer *o=context;
 return wr_action_channel_emit(&o->channel,WR_ACTION_ENDPOINT_PATH,e->uptime_ms,e);
}
static inline void wr_band_action_init(struct wr_band_action_observer *o){
 uint64_t session=0;int fd,saved=errno;ssize_t n;
 memset(o,0,sizeof(*o));wr_action_channel_init(&o->channel);
 fd=open("/dev/urandom",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
 if(fd>=0){n=read(fd,&session,sizeof(session));close(fd);if(n!=(ssize_t)sizeof(session))session=0;}
 o->reporter.session=session;o->reporter.emit=wr_band_action_emit;o->reporter.context=o;errno=saved;
}
#endif
