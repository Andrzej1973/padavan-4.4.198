/* All access under MacTabLock; adapter lifetime pinned separately. This is
 * software execution exclusion, never proof of hardware/callback retirement. */
#ifndef WR_IOT_PEER_CLOSE_EXECUTOR_H
#define WR_IOT_PEER_CLOSE_EXECUTOR_H
enum wr_peer_close_lane {WR_PEER_CLOSE_NONE,WR_PEER_CLOSE_LEGACY,WR_PEER_CLOSE_CHECKED,WR_PEER_CLOSE_RESET};
struct wr_iot_peer_close_executor {unsigned int lane,running,retained;unsigned long serial;};
static inline void wr_iot_peer_close_executor_init(struct wr_iot_peer_close_executor *s){
 s->lane=0;s->running=0;s->retained=0;s->serial=0;
}
static inline int wr_iot_peer_close_executor_enter(struct wr_iot_peer_close_executor *s,
 unsigned int lane,unsigned long serial){
 if(!s||s->running||(lane!=WR_PEER_CLOSE_LEGACY&&lane!=WR_PEER_CLOSE_CHECKED&&lane!=WR_PEER_CLOSE_RESET)||
    (lane==WR_PEER_CLOSE_CHECKED?!serial:serial!=0))return 0;
 if(s->lane && (lane!=WR_PEER_CLOSE_CHECKED||s->lane!=lane||s->serial!=serial))return 0;
 s->lane=lane;s->serial=serial;s->running=1;return 1;
}
static inline int wr_iot_peer_close_executor_leave(struct wr_iot_peer_close_executor *s,
 unsigned int lane,unsigned long serial,int success,int started){
 if(!s||!s->running||s->lane!=lane||s->serial!=serial)return 0;
 s->running=0;
 if(success||(!started&&!s->retained))wr_iot_peer_close_executor_init(s);
 else s->retained=1;
 return 1;
}
static inline int wr_iot_peer_close_executor_idle(const struct wr_iot_peer_close_executor *s){
 return s&&!s->lane&&!s->running&&!s->retained&&!s->serial;
}
#endif
