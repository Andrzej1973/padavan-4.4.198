/* Unified files/UTS/ARP recovery; daemon readiness remains caller responsibility.
 * All participating writers must hold the same persistent service lock. */
#ifndef WR_IOT_SERVICE_STATE_H
#define WR_IOT_SERVICE_STATE_H
#include "service-transaction.h"
#include "uts-state.h"
#include "arp-restore.h"
struct wr_iot_service_state {
 struct wr_iot_service_transaction transaction;
 struct wr_iot_uts_state saved_uts,expected_uts;
 struct wr_iot_arp_state saved_arp,expected_arp;
 int sealed,uts_done;
};
static inline void wr_iot_service_state_init(struct wr_iot_service_state *s){
 memset(s,0,sizeof(*s));wr_iot_service_transaction_init(&s->transaction);
}
static inline int wr_iot_service_state_begin(struct wr_iot_service_state *s,const char *lock,const char *lan){
 if(!s||!wr_iot_service_transaction_begin(&s->transaction,lock))return 0;
 if(!wr_iot_uts_capture(&s->saved_uts)||!wr_iot_arp_capture(lan,&s->saved_arp)||!wr_iot_arp_valid(&s->saved_arp)){
  wr_iot_bundle_release(&s->transaction.files);wr_iot_service_lock_release(&s->transaction.lock);s->transaction.active=0;return 0;
 }
 s->sealed=0;s->uts_done=0;return 1;
}
static inline int wr_iot_service_state_seal(struct wr_iot_service_state *s,const char *lock){
 struct wr_iot_uts_state uts;struct wr_iot_arp_state arp;
 if(!s||s->sealed||!s->transaction.active||!wr_iot_service_lock_valid(&s->transaction.lock,lock)||
    !wr_iot_uts_capture(&uts)||!wr_iot_arp_capture(s->saved_arp.interface,&arp)||!wr_iot_arp_valid(&arp)||
    !wr_iot_service_transaction_seal(&s->transaction,lock))return 0;
 s->expected_uts=uts;s->expected_arp=arp;s->sealed=1;return 1;
}
static inline int wr_iot_service_state_recover(struct wr_iot_service_state *s,const char *lock){
 struct wr_iot_uts_state current;int files,arp,uts=0;
 if(!s||!s->sealed||!s->transaction.active||!wr_iot_service_lock_valid(&s->transaction.lock,lock))return 0;
 files=wr_iot_service_transaction_restore(&s->transaction,lock);
 arp=wr_iot_arp_recover(&s->saved_arp,&s->expected_arp);
 if(wr_iot_uts_capture(&current)&&!strcmp(current.hostname,s->expected_uts.hostname)&&!strcmp(current.domain,s->expected_uts.domain)){
  if(!sethostname(s->saved_uts.hostname,strlen(s->saved_uts.hostname))){
   strcpy(s->expected_uts.hostname,s->saved_uts.hostname);
   if(!setdomainname(s->saved_uts.domain,strlen(s->saved_uts.domain))){
    strcpy(s->expected_uts.domain,s->saved_uts.domain);
    uts=wr_iot_uts_capture(&current)&&!strcmp(current.hostname,s->saved_uts.hostname)&&!strcmp(current.domain,s->saved_uts.domain);
   }
  }
 }
 s->uts_done=uts;return files&&arp&&uts;
}
/* Caller verifies daemon recovery/start before releasing retained backups. */
static inline int wr_iot_service_state_finish(struct wr_iot_service_state *s,const char *lock){
 if(!s||!s->sealed||!wr_iot_service_transaction_finish(&s->transaction,lock))return 0;
 s->sealed=0;return 1;
}
#endif
