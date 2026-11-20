/* Prepared adapter-owned storage. Initialize once, on fresh allocation only.
 * No pointer into a synchronous AUTH stack may be stored here. */
#ifndef WR_FT_IAPP_REQUEST_STATE_H
#define WR_FT_IAPP_REQUEST_STATE_H
#include "ft-iapp-response-token.h"
struct wr_ft_iapp_request_state {
 struct wr_ft_iapp_token_ledger ledger;
 struct wr_ft_iapp_token_handle current[WR_FT_IAPP_TOKEN_CAPACITY];
};
static inline void wr_ft_iapp_request_state_init(struct wr_ft_iapp_request_state *state)
{
 unsigned int i;
 if(!state)return;
 wr_ft_iapp_token_ledger_init(&state->ledger);
 for(i=0;i<WR_FT_IAPP_TOKEN_CAPACITY;i++)
  wr_ft_iapp_token_clear(&state->current[i]);
}
#endif
