/* Isolated model. Every operation requires one adapter-lifetime IRQ-safe
 * lock. A normal lease spans the whole send/wait and final queue transfer.
 * No queue/DMA/firmware epoch proof is implied. No reopen without such proof. */
#ifndef WR_IOT_MCU_SENDER_OWNER_H
#define WR_IOT_MCU_SENDER_OWNER_H
struct wr_iot_mcu_sender_owner {
 unsigned long close_serial;
 unsigned int inflight,closed,off_active,off_done,uncertain,poisoned,release_claimed;
};
static inline void wr_iot_mcu_sender_init(struct wr_iot_mcu_sender_owner *s)
{ s->close_serial=0;s->inflight=0;s->closed=0;s->off_active=0;s->off_done=0;s->uncertain=0;s->poisoned=0;s->release_claimed=0; }
static inline int wr_iot_mcu_sender_enter(struct wr_iot_mcu_sender_owner *s)
{
 if(!s||s->closed||s->poisoned||s->release_claimed)return 0;
 if(s->inflight==~0U){s->poisoned=1;s->closed=1;return 0;}
 s->inflight++;return 1;
}
static inline int wr_iot_mcu_sender_leave(struct wr_iot_mcu_sender_owner *s)
{
 if(!s||!s->inflight){if(s){s->poisoned=1;s->closed=1;}return 0;}
 s->inflight--;return 1;
}
static inline int wr_iot_mcu_sender_close(struct wr_iot_mcu_sender_owner *s,unsigned long serial)
{
 if(!s||!serial||s->poisoned||s->release_claimed)return 0;
 if(s->closed)return s->close_serial==serial;
 s->closed=1;s->close_serial=serial;return 1;
}
static inline int wr_iot_mcu_sender_off_begin(struct wr_iot_mcu_sender_owner *s,unsigned long serial)
{
 if(!s||!serial||!s->closed||s->close_serial!=serial||s->inflight||
    s->poisoned||s->uncertain||s->off_active||s->off_done||s->release_claimed)return 0;
 s->off_active=1;return 1;
}
/* success must come from a correctly correlated firmware ACK, not submission.
 * Failure retains uncertainty even if the transport returned an error. */
static inline int wr_iot_mcu_sender_off_finish(struct wr_iot_mcu_sender_owner *s,unsigned long serial,int success)
{
 if(!s||!serial||s->close_serial!=serial||!s->closed||!s->off_active||
    s->inflight||s->poisoned||s->uncertain||s->off_done)return 0;
 s->off_active=0;if(success==1)s->off_done=1;else s->uncertain=1;return 1;
}
/* Software sender drain only. Caller holds adapter-lifetime lock and has
 * separately retired every future caller before releasing adapter storage.
 * An uncertain OFF result blocks release even when its C invocation returned.
 * Hardware, message queues and RX callbacks require separate completion proof. */
static inline int wr_iot_mcu_sender_drained(const struct wr_iot_mcu_sender_owner *s)
{
 return s && s->closed && !s->inflight && !s->off_active &&
        !s->uncertain && !s->poisoned;
}

/* Claim under the same lock as OFF admission. It forbids a later OFF from
 * starting between the drain observation and actual adapter release.
 * All external caller references and hardware owners remain separate gates. */
static inline int wr_iot_mcu_sender_release_claim(struct wr_iot_mcu_sender_owner *s)
{
 if(!wr_iot_mcu_sender_drained(s)||s->release_claimed)return 0;
 s->release_claimed=1;return 1;
}

#endif
