#ifndef WR_STEERING_ACTION_H
#define WR_STEERING_ACTION_H
#include "action-event.h"
#include "../band-steering/protocol.h"
#include <errno.h>
#include <string.h>
struct wr_action_reporter {uint64_t session,sequence;unsigned int dropped;int (*emit)(const struct wr_action_event *,void *);void *context;};
static inline void wr_action_report(struct wr_action_reporter *r,struct wr_action_event *e){
 int saved=errno;
 if(!r||!r->session||!r->emit)return;
 if(r->sequence>=9007199254740991ULL){if(r->dropped<~0U)r->dropped++;errno=saved;return;}
 e->session=r->session;e->sequence=++r->sequence;
 if(!wr_action_valid(e)||!r->emit(e,r->context)){if(r->dropped<~0U)r->dropped++;}
 errno=saved;
}
/* Actual command function runs exactly once. Reporting does not change its
 * result or errno, including when the collector is absent or full. */
static inline int wr_action_steering_command(struct wr_action_reporter *reporter,
 unsigned int radio,uint64_t now,enum wr_band_protocol protocol,
 const struct wr_band_request *request,int (*command)(enum wr_band_protocol,const struct wr_band_request *,void *),void *context){
 struct wr_action_event e;int result,saved,report;
 if(!command||!request){errno=EINVAL;return -1;}
 report=radio<2&&(request->command==WR_ADD||request->command==WR_DELETE);
 memset(&e,0,sizeof(e));
 if(report){e.source=WR_ACTION_STEERING;e.operation=request->command==WR_ADD?WR_ACTION_ALLOW:WR_ACTION_REMOVE_CANDIDATE;e.stage=WR_ACTION_INTENT;e.radio=radio;e.bss=0;e.uptime_ms=now;e.cookie=request->cookie;memcpy(e.mac,request->mac,6);wr_action_report(reporter,&e);}
 result=command(protocol,request,context);saved=errno;
 if(report){e.stage=result<0?WR_ACTION_IOCTL_FAILED:WR_ACTION_IOCTL_ACCEPTED;e.result=result<0?-saved:0;wr_action_report(reporter,&e);}
 errno=saved;return result;
}
#endif
