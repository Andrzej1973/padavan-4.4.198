/* Extend known per-BSS lists; caller classifies keys using driver parsers. */
#ifndef WR_IOT_PROFILE_LIST_H
#define WR_IOT_PROFILE_LIST_H
#include <stddef.h>
#include <string.h>
static inline int wr_iot_profile_list_remove(char *out,size_t capacity,const char *existing,const char *third){
 const char *first,*second;size_t n;
 if(!out||!existing||!third||strpbrk(existing,"\r\n")||strpbrk(third,";\r\n"))return 0;
 first=strchr(existing,';');if(!first)return 0;
 second=strchr(first+1,';');
 if(!second||strchr(second+1,';')||strcmp(second+1,third))return 0;
 n=(size_t)(second-existing);if(n>=capacity)return 0;
 memmove(out,existing,n);out[n]=0;return 1;
}
static int wr_iot_profile_list(char *out,size_t capacity,const char *existing,const char *third,int enabled) {
 size_t old_size,extra=0;const char *separator;
 if(!out||!existing)return 0;
 old_size=strlen(existing);
 if(enabled){
  if(!third||strpbrk(existing,"\r\n")||strpbrk(third,";\r\n"))return 0;
  separator=strchr(existing,';');
  if(!separator||strchr(separator+1,';'))return 0;
  extra=strlen(third)+1;
 }
 if(old_size>=capacity||extra>=capacity-old_size)return 0;
 /* All rejection conditions precede the first output write. */
 memmove(out,existing,old_size);
 if(enabled){out[old_size]=';';memmove(out+old_size+1,third,extra-1);}
 out[old_size+extra]='\0';return 1;
}
#endif
