#include "timer-task-owner.h"
#include <assert.h>
int main(void){struct wr_iot_timer_task_owner s;int first=0,other=0;unsigned long old,next;
wr_iot_timer_task_owner_init(&s);assert(wr_iot_timer_task_owner_idle_for(&s,&first));
old=wr_iot_timer_task_owner_begin(&s,&first);assert(old&&!wr_iot_timer_task_owner_idle_for(&s,&first));
assert(wr_iot_timer_task_owner_idle_for(&s,&other));
assert(!wr_iot_timer_task_owner_end(&s,&other,old)&&s.running==&first);
assert(!wr_iot_timer_task_owner_end(&s,&first,old+1)&&s.running==&first);
assert(wr_iot_timer_task_owner_end(&s,&first,old));
next=wr_iot_timer_task_owner_begin(&s,&first);assert(next>old);
assert(!wr_iot_timer_task_owner_end(&s,&first,old)&&!wr_iot_timer_task_owner_idle_for(&s,&first));
assert(wr_iot_timer_task_owner_end(&s,&first,next));
old=wr_iot_timer_task_owner_begin(&s,&first);assert(old);
assert(!wr_iot_timer_task_owner_begin(&s,&other)&&s.poisoned&&s.running==&first);
assert(!wr_iot_timer_task_owner_idle_for(&s,&other));
wr_iot_timer_task_owner_init(&s);s.serial=~0UL;assert(!wr_iot_timer_task_owner_begin(&s,&first)&&s.poisoned);
assert(!wr_iot_timer_task_owner_begin(0,&first));return 0;}
