#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include "ft-kdp-event-span.h"
int main(void){
 unsigned long c,h,n;
 for(c=0;c<=1024;c++)for(h=0;h<=8;h++)for(n=0;n<=1025;n++){
  int expected=h<=c&&n<=c-h;
  assert(wr_ft_kdp_event_fits(c,h,n,1)==expected);
  assert(wr_ft_kdp_event_fits(c,h,n,0)==(expected&&!n));
 }
 assert(!wr_ft_kdp_event_fits(1024,6,ULONG_MAX,1));
 assert(!wr_ft_kdp_event_fits(0,ULONG_MAX,0,1));
 assert(wr_ft_kdp_event_fits(ULONG_MAX,6,ULONG_MAX-6,1));
 puts("PASS | FT KDP event span | capacities 0-1024, header 0-8, payload 0-1025, absent payload and ULONG_MAX subtraction bounds");return 0;
}
