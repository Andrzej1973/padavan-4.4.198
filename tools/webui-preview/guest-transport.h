/* Candidate transport policy: non-safelisted request header is required.
 * This relies on the existing HTTP server rejecting cross-origin preflight;
 * production activation also requires actual dispatcher/authentication tests.
 */
#ifndef WR_MODERN_GUEST_TRANSPORT_H
#define WR_MODERN_GUEST_TRANSPORT_H
#include <string.h>
struct wr_modern_guest_transport {int seen,valid;};
static void wr_modern_guest_header(struct wr_modern_guest_transport *state,const char *value)
{
 const char *end;
 if(state->seen){state->valid=0;return;}
 state->seen=1;state->valid=0;
 if(!value)return;
 value+=strspn(value," \t");
 if(*value!='1')return;
 end=value+1;end+=strspn(end," \t\r\n");
 state->valid=!*end;
}
static int wr_modern_guest_transport_allowed(const struct wr_modern_guest_transport *state,
 int post,const char *file,const char *query)
{
 return state&&state->seen&&state->valid&&post&&file&&!strcmp(file,"start_apply.htm")&&(!query||!*query);
}
#endif
