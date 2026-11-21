/* Read-only validation before the legacy CGI decoder. Candidate component;
 * binding to exact-length body input is required before production activation.
 */
#ifndef WR_MODERN_FORM_H
#define WR_MODERN_FORM_H
#include <stddef.h>
#include <string.h>
static int wr_modern_hex(unsigned char c)
{
 if(c>='0'&&c<='9')return c-'0';
 if(c>='a'&&c<='f')return c-'a'+10;
 if(c>='A'&&c<='F')return c-'A'+10;
 return -1;
}
static int wr_modern_form(const char *body,size_t length)
{
 char names[64][64];size_t count=0,pos=0,i,n;unsigned int markers=0;
 if(!body||!length||length>8192)return 0;
 while(pos<length){
  n=0;if(count==64)return 0;
  while(pos<length&&body[pos]!='='){
   unsigned char c=(unsigned char)body[pos++];
   if(c=='%'){
    int a,b;if(pos+1>=length)return 0;
    a=wr_modern_hex((unsigned char)body[pos]);b=wr_modern_hex((unsigned char)body[pos+1]);
    if(a<0||b<0)return 0;
    c=(unsigned char)(a*16+b);pos+=2;
   }
   if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='.'||c=='-')||n>=63)return 0;
   names[count][n++]=(char)c;
  }
  if(!n||pos>=length)return 0;
  names[count][n]=0;pos++;
  for(i=0;i<count;i++)if(!strcmp(names[i],names[count]))return 0;
  if(!strcmp(names[count],"wr_modern_guest_version")||!strcmp(names[count],"wr_modern_wifi_version"))markers++;
  count++;
  while(pos<length&&body[pos]!='&'){
   unsigned char c=(unsigned char)body[pos++];
   if(c=='%'){
    int a,b;if(pos+1>=length)return 0;
    a=wr_modern_hex((unsigned char)body[pos]);b=wr_modern_hex((unsigned char)body[pos+1]);
    if(a<0||b<0||(a==0&&b==0))return 0;
    pos+=2;
   }else if(c<0x20||c==0x7f||c==';')return 0;
  }
  if(pos<length){pos++;if(pos==length)return 0;}
 }
 return markers==1;
}
#endif
