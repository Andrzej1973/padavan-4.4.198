/* Candidate scheduler-token retirement only. Caller holds the vendor IRQ
 * lock and has fenced every producer/consumer for the selected WCID.
 * Never compact: packet metadata may retain physical FIFO indices.
 * This is not packet cleanup, DMA/RX completion or WCID-reuse permission. */
#ifndef WR_IOT_WCID_FIFO_RETIREMENT_H
#define WR_IOT_WCID_FIFO_RETIREMENT_H
static inline int wr_iot_wcid_fifo_retire(unsigned char *tokens,
 unsigned int count,unsigned int *dequeue,unsigned int enqueue,
 unsigned char wcid,unsigned int *removed)
{
 unsigned int i,n=0,pos;
 if(!tokens||!dequeue||!removed||!count||*dequeue>=count||enqueue>=count||!wcid)
  return 0;
 for(i=0;i<count;i++)if(tokens[i]==wcid){tokens[i]=0;n++;}
 pos=*dequeue;
 for(i=0;i<count;i++){
  if(tokens[pos])break;
  if(++pos==count)pos=0;
 }
 *dequeue=(i==count)?enqueue:pos;
 *removed=n;return 1;
}
/* Shared selector must skip retired holes in BOTH scheduler modes. Empty
 * detection is bounded even when enq==deq previously denoted a full ring. */
static inline int wr_iot_wcid_fifo_head(const unsigned char *tokens,
 unsigned int count,unsigned int *dequeue,unsigned int enqueue,
 unsigned char *wcid)
{
 unsigned int pos,i;
 if(!tokens||!dequeue||!wcid||!count||*dequeue>=count||enqueue>=count)return -1;
 pos=*dequeue;
 for(i=0;i<count;i++){
  if(tokens[pos]){*dequeue=pos;*wcid=tokens[pos];return 1;}
  if(++pos==count)pos=0;
 }
 *dequeue=enqueue;*wcid=0;return 0;
}
#endif
