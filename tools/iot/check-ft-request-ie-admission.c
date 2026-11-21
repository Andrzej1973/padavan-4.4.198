#include <assert.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#define IE_FT_MDIE 54
#define IE_FT_FTIE 55
#define IE_RSN 48
#define IE_WPA 221
#define FT_R0KH_ID 3
#define FT_ROKH_ID_LEN 48
#define FT_R1KH_ID 1
#define FT_R1KH_ID_LEN 6
#define FT_GTK 2
/* Boundary layouts only. Target SDK header compilation is still required;
 * the admission header itself uses sizeof/offsetof of actual caller types. */
typedef struct {unsigned char bytes[3];} FT_MDIE;
typedef struct {unsigned char fixed[82],Option[0];} FT_FTIE;
typedef struct {unsigned char GtkSubIE[64];} FT_FTIE_INFO;
typedef struct {unsigned char RSN_IE[255];} FT_INFO;
#include "ft-request-ie-admission.h"
int main(void){
 for(unsigned id=0;id<256;id++)for(unsigned n=0;n<256;n++){
  unsigned char *p=calloc(1,n+2);assert(p);p[0]=id;p[1]=n;
  int expected=1;
  if(id==IE_FT_MDIE)expected=n==3;
  if(id==IE_FT_FTIE)expected=n==82; /* Extra zero subelements refused. */
  if(id==IE_RSN||id==IE_WPA)expected=n>=5&&n<=253;
  assert(wr_iot_ft_request_ies_admitted(p,n+2)==expected);
  assert(!wr_iot_ft_request_ies_admitted(p,n+1));free(p);
 }
 unsigned char p[150]={IE_FT_FTIE,148};p[84]=FT_GTK;p[85]=64;
 assert(wr_iot_ft_request_ies_admitted(p,sizeof(p)));
 p[85]=65;assert(!wr_iot_ft_request_ies_admitted(p,sizeof(p)));
 assert(wr_iot_ft_request_ies_admitted(NULL,0));return 0;
}
