/* Prepared framing only. Caller derives capacities from actual vendor types.
 * No allocation, lifetime, event semantics or authorization is established. */
#ifndef WR_FT_KDP_EVENT_SPAN_H
#define WR_FT_KDP_EVENT_SPAN_H
static inline int wr_ft_kdp_event_fits(unsigned long capacity,
 unsigned long header,unsigned long length,int payload_present)
{
 return header<=capacity&&length<=capacity-header&&
  (!length||payload_present==1);
}
#endif
