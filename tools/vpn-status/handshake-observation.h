#ifndef WR_HANDSHAKE_OBSERVATION_H
#define WR_HANDSHAKE_OBSERVATION_H
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#define WR_HANDSHAKE_PEERS 128
/* Counts describe sampled handshake timestamps, never route/Internet health. */
struct wr_handshake_observation {
 unsigned peers, never, recent, old, future;
 unsigned observer; /* 0 unknown, 1 standard wg tool, 2 awg tool; not route health */
 uint64_t youngest_age;
 int has_age;
};
static inline int wr_handshake_read(FILE *fp, uint64_t now, uint64_t recent_window,
                                   struct wr_handshake_observation *out)
{
 struct wr_handshake_observation result={0};
 char line[96], seen[WR_HANDSHAKE_PEERS][45];
 if(!fp || !out) return 0;
 while(fgets(line,sizeof(line),fp)) {
  size_t n=strlen(line),i;uint64_t stamp=0,age;char *p;
  if(result.peers==WR_HANDSHAKE_PEERS || n<47 || line[n-1]!='\n' ||
     line[43]!='=' || line[44]!='\t') return 0;
  for(i=0;i<43;i++) {
   unsigned char c=(unsigned char)line[i];
   if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='+'||c=='/'))return 0;
  }
  for(i=0;i<result.peers;i++)if(!memcmp(seen[i],line,44))return 0;
  memcpy(seen[result.peers],line,44);seen[result.peers][44]=0;
  line[n-1]=0;p=line+45;if(!*p)return 0;
  for(;*p;p++) {
   unsigned digit;
   if(*p<'0'||*p>'9')return 0;
   digit=(unsigned)(*p-'0');
   if(stamp>(UINT64_MAX-digit)/10)return 0;
   stamp=stamp*10+digit;
  }
  result.peers++;
  if(!stamp){result.never++;continue;}
  if(stamp>now){result.future++;continue;}
  age=now-stamp;
  if(age<=recent_window)result.recent++;else result.old++;
  if(!result.has_age || age<result.youngest_age)result.youngest_age=age;
  result.has_age=1;
 }
 if(ferror(fp))return 0;
 *out=result;return 1;
}
#endif
