#ifndef WR_MODERN_BODY_H
#define WR_MODERN_BODY_H
#include <stdio.h>
#include "modern-form.h"
static inline int wr_modern_content_length(const char *value)
{
 unsigned int number=0,digits=0;
 if(!value)return 0;
 value+=strspn(value," \t");
 if(*value=='0')return 0;
 while(*value>='0'&&*value<='9'){
  if(++digits>4)return 0;
  number=number*10+(unsigned int)(*value++-'0');
 }
 value+=strspn(value," \t\r\n");
 return digits&&!*value&&number>0&&number<=8192;
}
static inline int wr_modern_body_read(FILE *stream,char *buffer,size_t capacity,int length)
{
 size_t got,i;volatile unsigned char *wipe=(volatile unsigned char *)buffer;
 if(buffer)for(i=0;i<capacity;i++)wipe[i]=0;
 if(!stream||!buffer||length<=0||length>8192||(size_t)length>=capacity)return 0;
 got=fread(buffer,1,(size_t)length,stream);
 if(got!=(size_t)length||!wr_modern_form(buffer,got)){
  for(i=0;i<capacity;i++)wipe[i]=0;
  return 0;
 }
 buffer[got]=0;return 1;
}
#endif
