/* Prepared framing/copy-bound admission for FT_FillFtIeInfo. Caller derives
 * fixed_bytes from offsetof(FT_FTIE,Option), gtk_capacity from destination. */
#ifndef WR_IOT_FT_SUBELEMENT_BOUNDS_H
#define WR_IOT_FT_SUBELEMENT_BOUNDS_H
#include "ft-ie-span.h"
static inline int wr_iot_ft_subelements_bounded(const unsigned char *body,
 unsigned int length,unsigned int fixed_bytes,unsigned int gtk_capacity,
 unsigned int r0_id,unsigned int r0_capacity,unsigned int r1_id,
 unsigned int r1_length,unsigned int gtk_id)
{
 unsigned int span,n;const unsigned char *at;
 if(!body||length<fixed_bytes)return 0;
 at=body+fixed_bytes;length-=fixed_bytes;
 while(length){
  if(!wr_iot_ft_ie_span(at,length,&span))return 0;
  n=span-2;
  if(at[0]==r0_id&&(!n||n>r0_capacity))return 0;
  if(at[0]==r1_id&&n!=r1_length)return 0;
  if(at[0]==gtk_id&&(!n||n>gtk_capacity))return 0;
  /* Native parser stops on zero-length subelements; reject instead of
   * accepting unexamined trailing subelements as a validated full list. */
  if(!n)return 0;
  at+=span;length-=span;
 }
 return 1;
}
#endif
