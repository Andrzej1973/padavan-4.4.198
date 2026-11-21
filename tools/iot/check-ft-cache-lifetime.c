#include <assert.h>
#include <stdio.h>
#include "ft-cache-lifetime.h"

int main(void)
{
 unsigned int count,i;
 for(count=0;count<=8;count++){
  struct wr_ft_cache_lifetime s,other;
  struct wr_ft_cache_lease leases[8]={{0}},late={0};
  unsigned long init,destroy;
  wr_ft_cache_lifetime_init(&s);wr_ft_cache_lifetime_init(&other);
  assert(!wr_ft_cache_enter(&s,&late));
  init=wr_ft_cache_start(&s);assert(init);
  assert(!wr_ft_cache_start(&s)&&!wr_ft_cache_close(&s));
  assert(!wr_ft_cache_enter(&s,&late));
  assert(!wr_ft_cache_publish(&s,init+1,1));
  assert(wr_ft_cache_publish(&s,init,1));
  assert(!wr_ft_cache_publish(&s,init,1));
  for(i=0;i<count;i++){
   assert(wr_ft_cache_enter(&s,&leases[i]));
   assert(!wr_ft_cache_enter(&s,&leases[i]));
   assert(!wr_ft_cache_leave(&other,&leases[i]));
  }
  assert(wr_ft_cache_close(&s)&&wr_ft_cache_close(&s));
  assert(!wr_ft_cache_enter(&s,&late)&&!wr_ft_cache_start(&s));
  for(i=count;i>0;i--){
   assert(!wr_ft_cache_destroy_begin(&s));
   assert(wr_ft_cache_leave(&s,&leases[i-1]));
   assert(!wr_ft_cache_leave(&s,&leases[i-1]));
  }
  destroy=wr_ft_cache_destroy_begin(&s);assert(destroy>init);
  assert(!wr_ft_cache_enter(&s,&late)&&!wr_ft_cache_start(&s));
  assert(!wr_ft_cache_destroy_begin(&s)&&!wr_ft_cache_close(&s));
  assert(!wr_ft_cache_destroy_finish(&s,init,1));
  assert(!wr_ft_cache_destroy_finish(&s,destroy,1));
  assert(!wr_ft_cache_destroy_claim(&s,init));
  assert(wr_ft_cache_destroy_claim(&s,destroy));
  assert(!wr_ft_cache_destroy_claim(&s,destroy));
  assert(!wr_ft_cache_enter(&s,&late)&&!wr_ft_cache_start(&s));
  assert(wr_ft_cache_destroy_finish(&s,destroy,1));
  assert(!wr_ft_cache_destroy_finish(&s,destroy,1));
  init=wr_ft_cache_start(&s);assert(init>destroy);
  assert(wr_ft_cache_publish(&s,init,1));
  assert(wr_ft_cache_enter(&s,&late)&&wr_ft_cache_leave(&s,&late));
 }
 {
  struct wr_ft_cache_lifetime s;
  struct wr_ft_cache_lease lease={0};unsigned long serial;
  wr_ft_cache_lifetime_init(&s);s.owner.serial=~0UL;
  assert(!wr_ft_cache_start(&s)&&s.owner.poisoned);
  wr_ft_cache_lifetime_init(&s);serial=wr_ft_cache_start(&s);
  assert(!wr_ft_cache_publish(&s,serial,0)&&s.owner.active&&s.owner.poisoned);
  assert(!wr_ft_cache_start(&s)&&!wr_ft_cache_enter(&s,&lease));
  wr_ft_cache_lifetime_init(&s);serial=wr_ft_cache_start(&s);
  assert(wr_ft_cache_publish(&s,serial,1));s.owner.transactions=~0U;
  assert(!wr_ft_cache_enter(&s,&lease)&&s.owner.poisoned);
  wr_ft_cache_lifetime_init(&s);serial=wr_ft_cache_start(&s);
  assert(wr_ft_cache_publish(&s,serial,1)&&wr_ft_cache_close(&s));
  serial=wr_ft_cache_destroy_begin(&s);assert(serial);
  assert(wr_ft_cache_destroy_claim(&s,serial));
  assert(!wr_ft_cache_destroy_finish(&s,serial,0));
  assert(s.owner.active&&s.owner.closed&&s.owner.poisoned);
  assert(!wr_ft_cache_start(&s)&&!wr_ft_cache_enter(&s,&lease));
 }
 puts("PASS | FT cache lifetime | close rejects late ingress, drains 0-8 holders, exclusive init/destroy, exact tickets, reopen and failure retention");
 return 0;
}
