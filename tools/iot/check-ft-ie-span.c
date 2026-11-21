#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "ft-ie-span.h"
int main(void)
{
 unsigned int remaining,length,span;
 for(remaining=0;remaining<=257;remaining++){
  /* Exact allocation puts the boundary at the ASan redzone. */
  unsigned char *bytes=malloc(remaining?remaining:1);assert(bytes);
  memset(bytes,0,remaining?remaining:1);
  for(length=0;length<256;length++){
   if(remaining>=2)bytes[1]=(unsigned char)length;
   span=999;
   int ok=wr_iot_ft_ie_span(bytes,remaining,&span);
   assert(ok==(remaining>=2&&length<=remaining-2));
   if(ok)assert(span==length+2);else assert(span==999);
  }
  free(bytes);
 }
 {
  unsigned char valid[]={1,0,2,1,9,3,2,8,7};
  unsigned char truncated[]={1,0,2};
  assert(wr_iot_ft_ie_list_framed(valid,sizeof(valid)));
  assert(!wr_iot_ft_ie_list_framed(truncated,sizeof(truncated)));
  assert(wr_iot_ft_ie_list_framed(NULL,0));
  assert(!wr_iot_ft_ie_list_framed(NULL,1));
  assert(!wr_iot_ft_ie_span(valid,sizeof(valid),NULL));
 }
 return 0;
}
