/* Prepared deletion boundary. Caller holds MacTabLock, validated native slot
 * identity and delete/reset admission. Never call while an event owns WCID.
 * Validate the whole affected set before changing any request record. */
#ifndef WR_FT_IAPP_SLOT_RETIREMENT_H
#define WR_FT_IAPP_SLOT_RETIREMENT_H
#include "ft-iapp-request-state.h"
static inline int wr_ft_iapp_slot_retire_locked(RTMP_ADAPTER *ad,
 struct wr_ft_iapp_request_state *state,unsigned int w)
{
 unsigned int i;const struct wr_ft_iapp_token_handle *current;
 if(!ad||!state||w==RESERVED_WCID||w>=MAX_LEN_OF_MAC_TABLE||
    w>=WR_FT_IAPP_TOKEN_CAPACITY||ad->wr_assoc_event_users[w])return 0;
 current=&state->current[w];
 if(current->serial){
  const struct wr_ft_iapp_token_entry *request;
  if(current->slot>=WR_FT_IAPP_TOKEN_CAPACITY)return 0;
  request=&state->ledger.entry[current->slot];
  if(request->serial!=current->serial||request->wcid!=w)return 0;
 }else if(state->detached[w])return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_CAPACITY;i++){
  const struct wr_ft_iapp_token_entry *request=&state->ledger.entry[i];
  if(request->wcid==w&&request->state!=WR_FT_IAPP_TOKEN_FREE&&
     request->state!=WR_FT_IAPP_TOKEN_WAITING)return 0;
 }
 for(i=0;i<WR_FT_IAPP_TOKEN_CAPACITY;i++){
  struct wr_ft_iapp_token_entry *request=&state->ledger.entry[i];
  if(request->wcid==w&&request->state==WR_FT_IAPP_TOKEN_WAITING){
   request->state=WR_FT_IAPP_TOKEN_FREE;request->invalidated=1;
  }
 }
 wr_ft_iapp_token_clear(&state->current[w]);
 state->detached[w]=state->detached_sst[w]=0;
 state->preauth[w]=(struct wr_ft_preauth_identity){0};
 return 1;
}
#endif
