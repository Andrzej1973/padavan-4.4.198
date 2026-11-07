#include "peer-open-owner.h"
#include <assert.h>
int main(void){
 struct wr_iot_peer_table_owner table;struct wr_iot_peer_open_owner s;
 struct wr_iot_peer_open_ticket t={0},bad,old;int dev=0,other=0;unsigned long first,next;
 wr_iot_peer_table_owner_init(&table);wr_iot_peer_open_owner_init(&s);
 assert(!wr_iot_peer_open_begin(&s,&table,&dev,0,&t)&&!table.active&&!t.serial);
 assert(wr_iot_peer_open_begin(&s,&table,&dev,1,&t));old=t;
 assert(!wr_iot_peer_table_allows(&table,0));
 assert(!wr_iot_peer_open_insert_begin(&s,&table,&t));
 assert(!wr_iot_peer_open_finish(&s,&table,&t,1));
 bad=t;bad.device=&other;assert(!wr_iot_peer_open_startup(&s,&table,&bad));
 bad=t;bad.serial++;assert(!wr_iot_peer_open_startup(&s,&table,&bad));
 assert(wr_iot_peer_open_startup(&s,&table,&t));
 assert(!wr_iot_peer_open_startup(&s,&table,&t));
 first=wr_iot_peer_open_insert_begin(&s,&table,&t);assert(first);
 assert(!wr_iot_peer_open_insert_begin(&s,&table,&t));
 assert(!wr_iot_peer_open_finish(&s,&table,&t,1));
 assert(!wr_iot_peer_open_insert_end(&s,&table,&bad,first));
 assert(wr_iot_peer_open_insert_end(&s,&table,&t,first));
 next=wr_iot_peer_open_insert_begin(&s,&table,&t);assert(next>first);
 assert(!wr_iot_peer_open_insert_end(&s,&table,&t,first));
 assert(wr_iot_peer_open_insert_end(&s,&table,&t,next));
 assert(wr_iot_peer_open_finish(&s,&table,&t,1)&&!table.active);
 assert(!wr_iot_peer_open_finish(&s,&table,&old,1));
 assert(wr_iot_peer_open_begin(&s,&table,&dev,1,&t)&&t.serial>old.serial);
 assert(!wr_iot_peer_open_startup(&s,&table,&old));
 assert(wr_iot_peer_open_startup(&s,&table,&t));
 next=wr_iot_peer_open_insert_begin(&s,&table,&t);assert(next);
 assert(wr_iot_peer_open_finish(&s,&table,&t,0)&&table.retained&&table.active);
 assert(wr_iot_peer_open_insert_end(&s,&table,&t,next));
 assert(!wr_iot_peer_open_finish(&s,&table,&t,1)&&table.retained);
 assert(!wr_iot_peer_open_begin(&s,&table,&dev,1,&bad));
 wr_iot_peer_table_owner_init(&table);wr_iot_peer_open_owner_init(&s);
 assert(wr_iot_peer_open_begin(&s,&table,&dev,1,&t));
 assert(wr_iot_peer_open_startup(&s,&table,&t));s.next_lease=~0UL;
 assert(!wr_iot_peer_open_insert_begin(&s,&table,&t)&&table.retained);
 return 0;
}
