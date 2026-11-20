#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ft-iapp-request-state.h"
int main(void)
{
 struct wr_ft_iapp_request_state state;
 unsigned char seed[7]={0},out[7],previous[7]={0};
 unsigned int i;
 memset(&state,0xa5,sizeof(state));wr_ft_iapp_request_state_init(&state);
 memset(out,9,sizeof(out));
 assert(!wr_ft_iapp_request_next_token_locked(&state,out));
 assert(!memcmp(out,seed,7));
 assert(wr_ft_iapp_request_state_seed(&state,seed));
 assert(!wr_ft_iapp_request_state_seed(&state,seed));
 assert(!wr_ft_iapp_request_next_token_locked(&state,state.token_counter));
 assert(!memcmp(state.token_counter,seed,7));
 for(i=0;i<1024;i++){
  assert(wr_ft_iapp_request_next_token_locked(&state,out));
  assert(wr_ft_iapp_token_nonzero(out)&&memcmp(out,previous,7)>0);
  assert(out[5]==(unsigned char)((i+1)>>8)&&out[6]==(unsigned char)(i+1));
  memcpy(previous,out,7);
 }
 /* Ledger cleanup must not reset sequence history. */
 wr_ft_iapp_token_ledger_init(&state.ledger);
 assert(wr_ft_iapp_request_next_token_locked(&state,out));
 assert(memcmp(out,previous,7)>0);
 memset(&state,0,sizeof(state));memset(seed,255,sizeof(seed));seed[6]=254;
 assert(wr_ft_iapp_request_state_seed(&state,seed));
 assert(wr_ft_iapp_request_next_token_locked(&state,out));
 for(i=0;i<7;i++)assert(out[i]==255);
 assert(!wr_ft_iapp_request_next_token_locked(&state,out));
 assert(state.token_exhausted&&!wr_ft_iapp_token_nonzero(out));
 assert(!wr_ft_iapp_request_state_seed(&state,seed));
 assert(!wr_ft_iapp_request_next_token_locked(&state,out));
 puts("PASS | FT token sequence | seed once, nonzero monotonic tokens, carry, ledger cleanup preserves sequence, output alias refusal, terminal overflow without reuse");
 return 0;
}
