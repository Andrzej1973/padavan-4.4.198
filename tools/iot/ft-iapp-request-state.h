/* Prepared adapter-owned storage. Initialize once, on fresh allocation only.
 * No pointer into a synchronous AUTH stack may be stored here. */
#ifndef WR_FT_IAPP_REQUEST_STATE_H
#define WR_FT_IAPP_REQUEST_STATE_H
#include "ft-iapp-response-token.h"
struct wr_ft_iapp_request_state {
 struct wr_ft_iapp_token_ledger ledger;
 struct wr_ft_iapp_token_handle current[WR_FT_IAPP_TOKEN_CAPACITY];
 unsigned char token_counter[WR_FT_IAPP_TOKEN_BYTES];
 unsigned int token_seeded,token_exhausted;
};
static inline void wr_ft_iapp_request_state_init(struct wr_ft_iapp_request_state *state)
{
 unsigned int i;
 if(!state)return;
 wr_ft_iapp_token_ledger_init(&state->ledger);
 state->token_seeded=state->token_exhausted=0;
 for(i=0;i<WR_FT_IAPP_TOKEN_BYTES;i++)state->token_counter[i]=0;
 for(i=0;i<WR_FT_IAPP_TOKEN_CAPACITY;i++)
  wr_ft_iapp_token_clear(&state->current[i]);
}
/* Seed only during fresh allocation, before publishing the adapter. */
static inline int wr_ft_iapp_request_state_seed(struct wr_ft_iapp_request_state *state,
 const unsigned char *seed)
{
 unsigned int i;
 if(!state||!seed||state->token_seeded||state->token_exhausted)return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_BYTES;i++)state->token_counter[i]=seed[i];
 state->token_seeded=1;
 return 1;
}
/* Caller holds MacTabLock. Never recycle a token after timeout or ledger-slot
 * reuse. Overflow seals publication until the adapter itself is destroyed. */
static inline int wr_ft_iapp_request_next_token_locked(struct wr_ft_iapp_request_state *state,
 unsigned char *token)
{
 unsigned int i,carry=1;
 if(!token)return 0;
 if(state&&token==state->token_counter)return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_BYTES;i++)token[i]=0;
 if(!state||!state->token_seeded||state->token_exhausted)return 0;
 for(i=WR_FT_IAPP_TOKEN_BYTES;i>0;i--){
  if(state->token_counter[i-1]!=255){carry=0;break;}
 }
 if(carry){state->token_exhausted=1;return 0;}
 for(i=WR_FT_IAPP_TOKEN_BYTES;i>0;i--){
  state->token_counter[i-1]++;
  if(state->token_counter[i-1])break;
 }
 for(i=0;i<WR_FT_IAPP_TOKEN_BYTES;i++)token[i]=state->token_counter[i];
 return 1;
}
#endif
