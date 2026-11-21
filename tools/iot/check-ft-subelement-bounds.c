#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "ft-subelement-bounds.h"
int main(void)
{
 unsigned int id,n;
 for(id=1;id<=4;id++)for(n=0;n<256;n++){
  unsigned int size=82+2+n;
  unsigned char *p=calloc(1,size);assert(p);p[82]=id;p[83]=n;
  int expected=n>0;
  if(id==1)expected=n==6;
  if(id==2)expected=n>0&&n<=32;
  if(id==3)expected=n>0&&n<=48;
  assert(wr_iot_ft_subelements_bounded(p,size,82,32,3,48,1,6,2)==expected);
  assert(!wr_iot_ft_subelements_bounded(p,size-1,82,32,3,48,1,6,2));
  free(p);
 }
 {
  unsigned char fixed[82]={0},truncated[83]={0};
  assert(wr_iot_ft_subelements_bounded(fixed,82,82,32,3,48,1,6,2));
  assert(!wr_iot_ft_subelements_bounded(fixed,81,82,32,3,48,1,6,2));
  assert(!wr_iot_ft_subelements_bounded(truncated,83,82,32,3,48,1,6,2));
  assert(!wr_iot_ft_subelements_bounded(NULL,82,82,32,3,48,1,6,2));
 }
 return 0;
}
