/* Prepared value-only MLME sidecar. Queue lock protects publication; consumer
 * owns dequeued element. No peer ownership or current-generation recapture. */
#ifndef WR_FT_PREAUTH_QUEUE_H
#define WR_FT_PREAUTH_QUEUE_H
#include "ft-iapp-request-state.h"
static inline void wr_ft_preauth_elem_clear(MLME_QUEUE_ELEM *event)
{
 unsigned int i;
 event->ft_preauth_serial=event->ft_preauth_generation=0;
 event->ft_preauth_wcid=event->ft_preauth_bss=0;
 for(i=0;i<6;i++)event->ft_preauth_mac[i]=event->ft_preauth_bssid[i]=0;
}
static inline int wr_ft_preauth_elem_publish(MLME_QUEUE_ELEM *event,
 const struct wr_ft_preauth_identity *identity)
{
 unsigned int i;
 if(!event||!identity||!identity->serial||!identity->generation||
    !identity->wcid||identity->wcid>=WR_FT_IAPP_TOKEN_CAPACITY||
    event->ft_preauth_serial)return 0;
 event->ft_preauth_generation=identity->generation;
 event->ft_preauth_wcid=identity->wcid;event->ft_preauth_bss=identity->bss;
 for(i=0;i<6;i++){
  event->ft_preauth_mac[i]=identity->mac[i];
  event->ft_preauth_bssid[i]=identity->bssid[i];
 }
 event->ft_preauth_serial=identity->serial;return 1;
}
static inline int wr_ft_preauth_elem_snapshot(const MLME_QUEUE_ELEM *event,
 struct wr_ft_preauth_identity *out)
{
 unsigned int i;
 if(!out)return 0;
 *out=(struct wr_ft_preauth_identity){0};
 if(!event||!event->ft_preauth_serial||!event->ft_preauth_generation||
    !event->ft_preauth_wcid||event->ft_preauth_wcid>=WR_FT_IAPP_TOKEN_CAPACITY)return 0;
 out->serial=event->ft_preauth_serial;out->generation=event->ft_preauth_generation;
 out->wcid=event->ft_preauth_wcid;out->bss=event->ft_preauth_bss;
 for(i=0;i<6;i++){out->mac[i]=event->ft_preauth_mac[i];out->bssid[i]=event->ft_preauth_bssid[i];}
 return 1;
}
#endif
