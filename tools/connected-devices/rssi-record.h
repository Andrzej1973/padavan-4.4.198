#ifndef WR_RSSI_RECORD_H
#define WR_RSSI_RECORD_H
/* Kernel-compatible bounded evidence storage. The caller must hold its
 * observer lock for every append/read. No allocation, logging or I/O here.
 * Capture identity before clearing the station table; radio/BSS identify
 * the original client. Submission never means over-the-air acknowledgement.
 * Not integrated into either driver yet. */
#define WR_RSSI_RECORD_CAPACITY 64
#define WR_RSSI_DECISION 1
#define WR_RSSI_ALLOCATION_FAILED 2
#define WR_RSSI_FRAME_SUBMITTED 3
#define WR_RSSI_ENTRY_CLEARED 4
struct wr_rssi_record {
 unsigned long long sequence, uptime_ms;
 unsigned int attempt;
 unsigned char mac[6],radio,bss,stage;
};
struct wr_rssi_records {
 struct wr_rssi_record entries[WR_RSSI_RECORD_CAPACITY];
 unsigned long long sequence, overwritten;
 unsigned int next,count,attempt_sequence;
};
static inline int wr_rssi_record_append(struct wr_rssi_records *ring,
 const struct wr_rssi_record *record)
{
 unsigned int i; unsigned char any=0;
 struct wr_rssi_record value;
 if(!ring||!record||ring->next>=WR_RSSI_RECORD_CAPACITY||
    ring->count>WR_RSSI_RECORD_CAPACITY||!record->attempt||
    record->radio>1||record->bss>15||record->stage<WR_RSSI_DECISION||
    record->stage>WR_RSSI_ENTRY_CLEARED||(record->mac[0]&1))return 0;
 for(i=0;i<6;i++)any|=record->mac[i];
 if(!any||ring->sequence==~0ULL)return 0;
 value=*record;value.sequence=++ring->sequence;
 ring->entries[ring->next]=value;
 ring->next=(ring->next+1)%WR_RSSI_RECORD_CAPACITY;
 if(ring->count<WR_RSSI_RECORD_CAPACITY)ring->count++;
 else if(ring->overwritten!=~0ULL)ring->overwritten++;
 return 1;
}
/* Reserve a never-reused attempt within this observer lifetime and append
 * its decision atomically under the caller's observer lock. Exhaustion
 * disables new observation attempts; it must not change driver behavior.
 * A separate driver-instance session is required across adapter restarts. */
static inline int wr_rssi_record_begin(struct wr_rssi_records *ring,
 struct wr_rssi_record *identity)
{
 struct wr_rssi_record value;
 if(!ring||!identity||ring->attempt_sequence==~0U)return 0;
 value=*identity;value.attempt=ring->attempt_sequence+1;
 value.stage=WR_RSSI_DECISION;
 if(!wr_rssi_record_append(ring,&value))return 0;
 ring->attempt_sequence=value.attempt;*identity=value;
 return 1;
}
/* Copy oldest available records after the caller's cursor. Hold the same
 * observer lock as append. Capacity bounds CPU work and output writes.
 * Caller also exports overwritten/sequence so missing history is explicit.
 * A future cursor is rejected: it may belong to a previous driver session. */
static inline int wr_rssi_record_read(const struct wr_rssi_records *ring,
 unsigned long long after,struct wr_rssi_record *output,unsigned int capacity)
{
 unsigned int i,index,count=0;
 if(!ring||!output||!capacity||capacity>WR_RSSI_RECORD_CAPACITY||
    ring->next>=WR_RSSI_RECORD_CAPACITY||ring->count>WR_RSSI_RECORD_CAPACITY||
    after>ring->sequence)return -1;
 index=(ring->next+WR_RSSI_RECORD_CAPACITY-ring->count)%WR_RSSI_RECORD_CAPACITY;
 for(i=0;i<ring->count&&count<capacity;i++){
  const struct wr_rssi_record *entry=&ring->entries[(index+i)%WR_RSSI_RECORD_CAPACITY];
  if(entry->sequence>after)output[count++]=*entry;
 }
 return (int)count;
}
#endif
