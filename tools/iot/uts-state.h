/* Caller serializes hostname/domain writers during the service transaction. */
#ifndef WR_IOT_UTS_STATE_H
#define WR_IOT_UTS_STATE_H
#include <unistd.h>
#include <string.h>
struct wr_iot_uts_state {char hostname[256],domain[256];};
static inline int wr_iot_uts_capture(struct wr_iot_uts_state *out){
 struct wr_iot_uts_state candidate;
 if(!out)return 0;
 memset(&candidate,0,sizeof(candidate));
 if(gethostname(candidate.hostname,sizeof(candidate.hostname))||getdomainname(candidate.domain,sizeof(candidate.domain))||
    !memchr(candidate.hostname,0,sizeof(candidate.hostname))||!memchr(candidate.domain,0,sizeof(candidate.domain)))return 0;
 *out=candidate;return 1;
}
/* Report any partial error; retain captured state for retry, never claim full recovery. */
static inline int wr_iot_uts_restore(const struct wr_iot_uts_state *saved){
 if(!saved||!memchr(saved->hostname,0,sizeof(saved->hostname))||!memchr(saved->domain,0,sizeof(saved->domain)))return 0;
 if(sethostname(saved->hostname,strlen(saved->hostname)))return 0;
 return setdomainname(saved->domain,strlen(saved->domain))==0;
}
#endif
