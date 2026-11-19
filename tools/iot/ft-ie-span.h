/* Bounded TLV framing only: callers must still validate per-IE semantics.
 * No header byte is read before at least two bytes are known available. */
#ifndef WR_IOT_FT_IE_SPAN_H
#define WR_IOT_FT_IE_SPAN_H
static inline int wr_iot_ft_ie_span(const unsigned char *bytes,
 unsigned int remaining,unsigned int *span)
{
 unsigned int length;
 if(!bytes||!span||remaining<2)return 0;
 length=bytes[1];
 if(length>remaining-2)return 0;
 *span=length+2;return 1;
}
static inline int wr_iot_ft_ie_list_framed(const unsigned char *bytes,
 unsigned int remaining)
{
 unsigned int span;
 if(!bytes&&remaining)return 0;
 while(remaining){
  if(!wr_iot_ft_ie_span(bytes,remaining,&span))return 0;
  bytes+=span;remaining-=span;
 }
 return 1;
}
#endif
