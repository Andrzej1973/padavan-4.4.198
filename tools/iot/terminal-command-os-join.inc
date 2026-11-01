/* Candidate command-task identity boundary. Creation failure ERR_PTR is
 * unknown/unjoinable, never a valid task for kthread_stop. */
INT wr_iot_os_command_task_current(RTMP_OS_TASK *task)
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
 if (IS_ERR_OR_NULL(native->kthread_task)) return -1;
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
