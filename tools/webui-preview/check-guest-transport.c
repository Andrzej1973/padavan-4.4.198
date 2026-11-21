#include <assert.h>
#include <stdio.h>
#include "guest-transport.h"
int main(void)
{
 struct wr_modern_guest_transport state={0};
 assert(!wr_modern_guest_transport_allowed(&state,1,"start_apply.htm",NULL));
 wr_modern_guest_header(&state," 1\r\n");
 assert(wr_modern_guest_transport_allowed(&state,1,"start_apply.htm",NULL));
 assert(!wr_modern_guest_transport_allowed(&state,0,"start_apply.htm",NULL));
 assert(!wr_modern_guest_transport_allowed(&state,1,"apply.cgi",NULL));
 assert(!wr_modern_guest_transport_allowed(&state,1,"start_apply.htm","x=1"));
 wr_modern_guest_header(&state,"1");assert(!state.valid);
 const char *bad[]={NULL,"","0","11","1,1","true","1 trailing","1\r\nX:1"};
 for(unsigned int i=0;i<sizeof(bad)/sizeof(bad[0]);i++){
  state=(struct wr_modern_guest_transport){0};wr_modern_guest_header(&state,bad[i]);assert(!state.valid);
  wr_modern_guest_header(&state,"1");assert(!state.valid);
 }
 puts("PASS Guest transport component: exact header, duplicates rejected, POST/exact route/no query; not browser/dispatcher/auth acceptance");return 0;
}
