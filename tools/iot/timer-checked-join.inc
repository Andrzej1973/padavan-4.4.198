/* Exclusive timer + adapter/module ownership required. Never call under
 * MAC/IRQ/transition/TimerQLock, in atomic context, or from this timer task.
 * No resource is freed here. Boolean success concerns timer paths only. */
#ifdef RTMP_TIMER_TASK_SUPPORT
static BOOLEAN wr_iot_timer_task_idle(RTMP_ADAPTER *pAd,RALINK_TIMER_STRUCT *timer)
{
 ULONG flags;
 BOOLEAN idle;
 RTMP_INT_LOCK(&pAd->TimerQLock,flags);
 idle = wr_iot_timer_task_owner_idle_for(&pAd->wr_iot_timer_owner,timer);
 RTMP_INT_UNLOCK(&pAd->TimerQLock,flags);
 return idle;
}

static VOID wr_iot_timer_remove_all_queued(RTMP_ADAPTER *pAd,RALINK_TIMER_STRUCT *timer)
{
 RTMP_TIMER_TASK_ENTRY *node,*previous = NULL,*next;
 ULONG flags;
 RTMP_INT_LOCK(&pAd->TimerQLock,flags);
 node = pAd->TimerQ.pQHead;
 while (node) {
  next = node->pNext;
  if (node->pRaTimer == timer) {
   if (previous) previous->pNext = next;else pAd->TimerQ.pQHead = next;
   if (pAd->TimerQ.pQTail == node) pAd->TimerQ.pQTail = previous;
   node->pNext = pAd->TimerQ.pQPollFreeList;pAd->TimerQ.pQPollFreeList = node;
  } else previous = node;
  node = next;
 }
 RTMP_INT_UNLOCK(&pAd->TimerQLock,flags);
}
#endif

BOOLEAN wr_iot_timer_join_checked(RTMP_ADAPTER *pAd,RALINK_TIMER_STRUCT *timer,
 ULONG timeout_ms)
{
 if (!pAd || !timer || !timeout_ms || timeout_ms > 5000 ||
     wr_iot_os_join_context() || !READ_ONCE(timer->Valid) || timer->pAd != pAd)
  return FALSE;
#ifdef RTMP_TIMER_TASK_SUPPORT
 if (!(READ_ONCE(pAd->TimerQ.status) & RTMP_TASK_CAN_DO_INSERT) ||
     wr_iot_os_timer_task_current(&pAd->timerTask) != 0) return FALSE;
#endif
 wr_iot_timer_fence(timer);
 if (!READ_ONCE(timer->wr_iot_retiring) || wr_iot_os_sync_timer(&timer->TimerObj))
  return FALSE;
#ifdef RTMP_TIMER_TASK_SUPPORT
 wr_iot_timer_remove_all_queued(pAd,timer);
 if (!wait_event_timeout(pAd->wr_iot_timer_drain_wait,
       wr_iot_timer_task_idle(pAd,timer),msecs_to_jiffies(timeout_ms))) return FALSE;
#endif
 /* A task callback admitted before the fence could have rearmed after the
  * first OS sync. Join that timer after the task has finished all accesses. */
 if (wr_iot_os_sync_timer(&timer->TimerObj)) return FALSE;
#ifdef RTMP_TIMER_TASK_SUPPORT
 wr_iot_timer_remove_all_queued(pAd,timer);
 if (!wr_iot_timer_task_idle(pAd,timer)) return FALSE;
#endif
 return READ_ONCE(timer->Valid) && READ_ONCE(timer->wr_iot_retiring);
}
