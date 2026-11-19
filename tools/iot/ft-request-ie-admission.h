/* Requires vendor FT types/IDs. Prepared admission before FT_ReqActionParse;
 * validation is read-only and must precede native output/station mutation. */
#ifndef WR_IOT_FT_REQUEST_IE_ADMISSION_H
#define WR_IOT_FT_REQUEST_IE_ADMISSION_H
#include "ft-subelement-bounds.h"
static inline int wr_iot_ft_request_ies_admitted(const unsigned char *at,
 unsigned int remaining)
{
 unsigned int span,length;
 if(!at&&remaining)return 0;
 while(remaining){
  if(!wr_iot_ft_ie_span(at,remaining,&span))return 0;
  length=span-2;
  if(at[0]==IE_FT_MDIE&&length!=sizeof(FT_MDIE))return 0;
  if(at[0]==IE_FT_FTIE&&
     !wr_iot_ft_subelements_bounded(at+2,length,
      offsetof(FT_FTIE,Option),sizeof(((FT_FTIE_INFO *)0)->GtkSubIE),
      FT_R0KH_ID,FT_ROKH_ID_LEN,FT_R1KH_ID,FT_R1KH_ID_LEN,FT_GTK))return 0;
  if(at[0]==IE_RSN||at[0]==IE_WPA){
   /* Native OUI alternatives inspect bytes0..3 and2..4 unconditionally.
    * Its output length is UCHAR, so span must also fit without truncation. */
   if(length<5||span>255||span>sizeof(((FT_INFO *)0)->RSN_IE))return 0;
  }
  at+=span;remaining-=span;
 }
 return 1;
}
#endif
