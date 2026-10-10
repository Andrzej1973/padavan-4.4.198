#include "action-owner.h"
#include <assert.h>
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
 puts("PASS actual proc starttime and exclusive flock evidence parsing");return 0;
}
