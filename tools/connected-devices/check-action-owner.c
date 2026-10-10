#include "action-owner.h"
#include <assert.h>
#include <sys/file.h>
int main(void){
 char stat[512];uint64_t birth=0;unsigned i;size_t n;
 strcpy(stat,"123 (name ) with spaces) S");n=strlen(stat);
 for(i=4;i<22;i++)n+=(size_t)snprintf(stat+n,sizeof(stat)-n," 0");
 snprintf(stat+n,sizeof(stat)-n," 987654 0\n");
 assert(wr_action_birth_parse(stat,&birth)&&birth==987654);
 birth=42;assert(!wr_action_birth_parse("123 (x) S 1",&birth)&&birth==42);
 assert(wr_action_lock_matches("1: FLOCK ADVISORY WRITE 123 00:08:456 0 EOF\n",123,0,8,456));
 assert(!wr_action_lock_matches("1: -> FLOCK ADVISORY WRITE 123 00:08:456 0 EOF\n",123,0,8,456));
 assert(!wr_action_lock_matches("1: FLOCK ADVISORY READ 123 00:08:456 0 EOF\n",123,0,8,456));
 assert(!wr_action_lock_matches("1: FLOCK ADVISORY WRITE 124 00:08:456 0 EOF\n",123,0,8,456));
 assert(!wr_action_lock_matches("1: FLOCK ADVISORY WRITE 123 00:08:457 0 EOF\n",123,0,8,456));
 {
 char temporary[]="/tmp/wr-action-owner-XXXXXX",pidtext[32];int fd=mkstemp(temporary);struct wr_action_owner owner={0},saved;
 assert(fd>=0);assert(!fchmod(fd,0600));assert(!flock(fd,LOCK_EX|LOCK_NB));
 snprintf(pidtext,sizeof(pidtext),"%ld\n",(long)getpid());assert(write(fd,pidtext,strlen(pidtext))==(ssize_t)strlen(pidtext));
 assert(wr_action_owner_verify(temporary,"/proc/self/exe","/proc",geteuid(),&owner));assert(owner.pid==getpid()&&owner.birth);
 saved=owner;assert(!flock(fd,LOCK_UN));assert(!wr_action_owner_verify(temporary,"/proc/self/exe","/proc",geteuid(),&owner));assert(!memcmp(&owner,&saved,sizeof(owner)));
 assert(!flock(fd,LOCK_EX|LOCK_NB));assert(!wr_action_owner_verify(temporary,"/bin/sh","/proc",geteuid(),&owner));
 close(fd);unlink(temporary);
 }
 puts("PASS real process executable, birth and exclusive lock verification plus negative stale-lock checks");return 0;
}
