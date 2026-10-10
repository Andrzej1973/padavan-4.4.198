#ifndef WR_ACTION_OWNER_H
#define WR_ACTION_OWNER_H
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>
#include <sys/types.h>
/* Linux proc stat comm may contain spaces and closing parentheses. The final
 * closing parenthesis ends comm; field 22 is starttime, not a wall clock. */
static inline int wr_action_birth_parse(const char *text,uint64_t *out){
 const char *p,*end;char *tail;unsigned long long value;unsigned field;
 if(!text||!out||!(p=strrchr(text,')'))||p[1]!=' ')return 0;
 p+=2;
 for(field=3;field<=22;field++){
  while(*p==' ')p++;
  end=p;while(*end&&*end!=' '&&*end!='\n')end++;
  if(end==p)return 0;
  if(field==22){
   const char *digit;for(digit=p;digit<end;digit++)if(*digit<'0'||*digit>'9')return 0;
   errno=0;value=strtoull(p,&tail,10);
   if(errno||tail!=end||!value)return 0;
   *out=(uint64_t)value;return 1;
  }
  if(!*end||*end=='\n')return 0;
  p=end+1;
 }
 return 0;
}
/* Match the retained exclusive flock, not a blocked waiter (->), POSIX
 * record lock or another process. Layout verified against pinned fs/locks.c. */
static inline int wr_action_lock_matches(const char *line,pid_t pid,
 unsigned device_major,unsigned device_minor,unsigned long long inode){
 unsigned long long id,actual_inode;unsigned maj,min;long owner;char kind[16],mode[16],access[16],start[16],finish[16],extra;
 if(!line||pid<=0)return 0;
 if(sscanf(line,"%llu: %15s %15s %15s %ld %x:%x:%llu %15s %15s %c",
 &id,kind,mode,access,&owner,&maj,&min,&actual_inode,start,finish,&extra)!=9)return 0;
 return !strcmp(kind,"FLOCK")&&!strcmp(mode,"ADVISORY")&&!strcmp(access,"WRITE")&&
 owner==(long)pid&&maj==device_major&&min==device_minor&&actual_inode==inode&&
 !strcmp(start,"0")&&!strcmp(finish,"EOF");
}
#endif
