/* Linux utility boundary: no adapter layout dependency. Caller owns the timer.
 * del_timer_sync has no timeout; only the separate task wait is bounded. */
INT wr_iot_os_join_context(VOID)
{
 return (in_interrupt() || irqs_disabled() || in_atomic()) ? -1 : 0;
}

INT wr_iot_os_sync_timer(NDIS_MINIPORT_TIMER *timer)
{
 OS_NDIS_MINIPORT_TIMER *native;
 if (!timer || wr_iot_os_join_context()) return -1;
#ifdef OS_ABL_FUNC_SUPPORT
 native = (OS_NDIS_MINIPORT_TIMER *)timer->pContent;
#else
 native = (OS_NDIS_MINIPORT_TIMER *)timer;
#endif
 if (!native) return -1;
 (void)del_timer_sync(native); /* Always synchronize, including not-pending. */
 return 0;
}

/* -1 means unknown identity: callers must retain rather than wait on self. */
INT wr_iot_os_timer_task_current(RTMP_OS_TASK *task)
{
 OS_TASK *native;
 if (!task) return -1;
#ifdef OS_ABL_FUNC_SUPPORT
 native = (OS_TASK *)task->pContent;
#else
 native = (OS_TASK *)task;
#endif
 if (!native) return -1;
#ifdef KTHREAD_SUPPORT
 if (!native->kthread_task) return -1;
 return native->kthread_task == current;
#else
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,27)
 if (!native->taskPID) return -1;
 return native->taskPID == task_pid(current);
#else
 if (native->taskPID <= 0) return -1;
 return native->taskPID == current->pid;
#endif
#endif
}
