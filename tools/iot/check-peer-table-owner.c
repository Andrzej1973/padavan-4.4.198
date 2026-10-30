#include "peer-table-owner.h"
#include <assert.h>
int main(void){
 struct wr_iot_peer_table_owner s;unsigned long first,second;
 wr_iot_peer_table_owner_init(&s);
 assert(wr_iot_peer_table_allows(&s,0));
 first=wr_iot_peer_table_begin(&s);assert(first);
 assert(!wr_iot_peer_table_allows(&s,0));
 assert(wr_iot_peer_table_allows(&s,first));
 assert(!wr_iot_peer_table_begin(&s));
 assert(!wr_iot_peer_table_finish(&s,first+1,1));
 assert(!wr_iot_peer_table_finish(&s,0,1));
 assert(wr_iot_peer_table_finish(&s,first,1));
 assert(!wr_iot_peer_table_finish(&s,first,1));
 second=wr_iot_peer_table_begin(&s);assert(second>first);
 assert(!wr_iot_peer_table_allows(&s,first));
 assert(wr_iot_peer_table_finish(&s,second,0));
 assert(s.active&&s.retained&&!wr_iot_peer_table_allows(&s,0));
 assert(!wr_iot_peer_table_allows(&s,second));
 assert(!wr_iot_peer_table_finish(&s,second,1));
 assert(!wr_iot_peer_table_begin(&s));
 wr_iot_peer_table_owner_init(&s);s.serial=~0UL;
 assert(!wr_iot_peer_table_begin(&s)&&s.poisoned);
 assert(!wr_iot_peer_table_allows(&s,0));
 wr_iot_peer_table_owner_init(&s);
 assert(wr_iot_peer_table_transaction_enter(&s));
 assert(!wr_iot_peer_table_begin(&s));
 assert(wr_iot_peer_table_transaction_leave(&s));
 first=wr_iot_peer_table_begin(&s);assert(first);
 assert(wr_iot_peer_table_close_seal(&s,first));
 assert(s.closed&&!wr_iot_peer_table_allows(&s,0));
 assert(!wr_iot_peer_table_begin(&s));
 assert(!wr_iot_peer_table_transaction_enter(&s));
 second=wr_iot_peer_table_begin_open(&s);assert(second>first&&!s.closed);
 assert(wr_iot_peer_table_finish(&s,second,1));
 assert(!wr_iot_peer_table_transaction_leave(&s)&&s.poisoned);
 assert(!wr_iot_peer_table_begin_open(&s));
 assert(!wr_iot_peer_table_begin(0));
 assert(!wr_iot_peer_table_finish(0,1,1));
 return 0;
}
