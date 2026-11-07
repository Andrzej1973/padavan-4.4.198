#include <assert.h>
#include <stddef.h>
#define KERNEL_VERSION(a,b,c) (((a)<<16)|((b)<<8)|(c))
#define LINUX_VERSION_CODE KERNEL_VERSION(4,4,198)
typedef int INT;typedef void VOID;
typedef struct {int pending,running;} OS_NDIS_MINIPORT_TIMER;
struct pid {int number;};struct task_struct {struct pid *pid;};
typedef struct {struct task_struct *kthread_task;struct pid *taskPID;} OS_TASK;
#ifdef OS_ABL_FUNC_SUPPORT
typedef struct {void *pContent;} NDIS_MINIPORT_TIMER;
typedef struct {void *pContent;} RTMP_OS_TASK;
#else
typedef OS_NDIS_MINIPORT_TIMER NDIS_MINIPORT_TIMER;
typedef OS_TASK RTMP_OS_TASK;
#endif
static struct task_struct current_storage,*current=&current_storage;
static int interrupt_context,irq_off,atomic_context,joins;
#define in_interrupt() (interrupt_context)
#define irqs_disabled() (irq_off)
#define in_atomic() (atomic_context)
#define task_pid(t) ((t)->pid)
static int del_timer_sync(OS_NDIS_MINIPORT_TIMER *t){int pending=t->pending;joins++;t->pending=t->running=0;return pending;}
#include "wr-iot-timer-os-join.inc"
int main(void){OS_NDIS_MINIPORT_TIMER native={0,1};OS_TASK task={0};
static struct pid self_pid={1},other_pid={2};struct task_struct other={&other_pid};
NDIS_MINIPORT_TIMER *timer;RTMP_OS_TASK *wrapped_task;
#ifdef OS_ABL_FUNC_SUPPORT
NDIS_MINIPORT_TIMER timer_wrapper={&native};RTMP_OS_TASK task_wrapper={&task};
timer=&timer_wrapper;wrapped_task=&task_wrapper;
#else
timer=&native;wrapped_task=&task;
#endif
assert(!wr_iot_os_sync_timer(timer)&&joins==1&&!native.running); /* running, not pending */
interrupt_context=1;assert(wr_iot_os_sync_timer(timer)==-1&&joins==1);interrupt_context=0;
irq_off=1;assert(wr_iot_os_sync_timer(timer)==-1&&joins==1);irq_off=0;
atomic_context=1;assert(wr_iot_os_sync_timer(timer)==-1&&joins==1);atomic_context=0;
assert(wr_iot_os_sync_timer(NULL)==-1);
current->pid=&self_pid;
assert(wr_iot_os_timer_task_current(NULL)==-1);
assert(wr_iot_os_timer_task_current(wrapped_task)==-1);
task.kthread_task=&other;task.taskPID=&other_pid;
assert(wr_iot_os_timer_task_current(wrapped_task)==0);
task.kthread_task=current;task.taskPID=&self_pid;
assert(wr_iot_os_timer_task_current(wrapped_task)==1);
#ifdef OS_ABL_FUNC_SUPPORT
timer_wrapper.pContent=NULL;assert(wr_iot_os_sync_timer(timer)==-1);
task_wrapper.pContent=NULL;assert(wr_iot_os_timer_task_current(wrapped_task)==-1);
#endif
return 0;}
