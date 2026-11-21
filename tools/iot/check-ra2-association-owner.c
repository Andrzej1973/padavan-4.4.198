#include <assert.h>
#include <stdio.h>
#include "ra2-association-owner.h"
int main(void)
{
 struct wr_ra2_assoc_owner owner={0},other={0};
 struct wr_ra2_assoc_ticket a={0},b={0},key={0},foreign={0};
 assert(wr_ra2_assoc_enter(&owner,&a,0));
 assert(wr_ra2_assoc_enter(&owner,&b,0));
 assert(!wr_ra2_assoc_enter(&owner,&key,1));
 assert(!wr_ra2_assoc_enter(&owner,&a,0));
 assert(!wr_ra2_assoc_leave(&other,&a));assert(owner.associations==2);
 assert(wr_ra2_assoc_leave(&owner,&a));assert(!wr_ra2_assoc_leave(&owner,&a));
 assert(!wr_ra2_assoc_enter(&owner,&key,1));
 assert(wr_ra2_assoc_leave(&owner,&b));
 assert(wr_ra2_assoc_enter(&owner,&key,1));
 assert(!wr_ra2_assoc_enter(&owner,&a,0));
 assert(!wr_ra2_assoc_enter(&owner,&b,1));
 /* Independent adapters do not block one another. */
 assert(wr_ra2_assoc_enter(&other,&foreign,0));
 assert(wr_ra2_assoc_leave(&other,&foreign));
 assert(wr_ra2_assoc_leave(&owner,&key));
 assert(wr_ra2_assoc_enter(&owner,&a,0));
 assert(wr_ra2_assoc_leave(&owner,&a));
 /* A changed key token cannot release another writer. */
 assert(wr_ra2_assoc_enter(&owner,&key,1));
 owner.key_serial++;assert(!wr_ra2_assoc_leave(&owner,&key));
 assert(owner.poisoned&&owner.key_active==1&&key.active);
 assert(!wr_ra2_assoc_enter(&owner,&a,0));
 owner=(struct wr_ra2_assoc_owner){.serial=~0UL};
 a=(struct wr_ra2_assoc_ticket){0};
 assert(!wr_ra2_assoc_enter(&owner,&a,0));assert(owner.poisoned&&!a.active);
 owner=(struct wr_ra2_assoc_owner){.associations=~0U};
 assert(!wr_ra2_assoc_enter(&owner,&a,0));assert(owner.poisoned&&!a.active);
 puts("ra2 association/key arbitration: PASS; native driver binding not tested");
 return 0;
}
