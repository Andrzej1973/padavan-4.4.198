#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <errno.h>
static int mode,calls;
static int fake_random(void *out,unsigned int length,unsigned int flags){
 unsigned char *bytes=out;calls++;assert(length==32&&flags==1);
 if(mode<0){errno=-mode;return -1;}
 for(unsigned int i=0;i<length;i++)bytes[i]=(unsigned char)(i+1);
 return mode;
}
#define WR_IOT_GETRANDOM fake_random
#include "precreated-entropy.h"
int main(void){
 unsigned char bytes[32];
 assert(wr_iot_precreated_entropy(NULL,NULL,32)==-1);
 assert(wr_iot_precreated_entropy(NULL,bytes,31)==-1&&calls==0);
 int failures[]={-EAGAIN,-ENOSYS,-EINTR,0,31};
 for(unsigned i=0;i<sizeof(failures)/sizeof(*failures);i++){
  mode=failures[i];int result=wr_iot_precreated_entropy(NULL,bytes,32);
  assert(result== (mode<0?-1:mode));
 }
 mode=32;assert(wr_iot_precreated_entropy(NULL,bytes,32)==32);
 puts("PASS entropy adapter requests exactly32 bytes, nonblocking initialized kernel source; errors/short reads preserved for boot policy refusal; no retry/fallback.");return 0;
}
