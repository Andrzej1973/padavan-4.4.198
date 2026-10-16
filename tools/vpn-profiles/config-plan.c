#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "config-plan.h"
#include <arpa/inet.h>
#include <stdlib.h>
#include <strings.h>

static char *trim_field(char *s)
{
    size_t n;while (*s==' ' || *s=='\t') s++;
    n=strlen(s);while (n && (s[n-1]==' ' || s[n-1]=='\t' || s[n-1]=='\r')) s[--n]=0;
    return s;
}
static int append_text(char *out,size_t capacity,const char *value,const char *separator)
{
    size_t old=strlen(out),n=strlen(value),sep=old?strlen(separator):0;
    if (old+sep+n+1>capacity) return 0;
    if (sep) memcpy(out+old,separator,sep);
    memcpy(out+old+sep,value,n+1);return 1;
}
static void erase(void *data,size_t size)
{ volatile unsigned char *p=data;while (size--) *p++=0; }
enum wr_vpn_validation wr_vpn_prepare_config(const struct wr_vpn_record *record,struct wr_vpn_config_plan *out)
{
    struct wr_vpn_config_plan *plan;struct wr_vpn_resources resources;
    enum wr_vpn_validation result;char *text,*cursor,*next,*line,*equal,*key,*value,*comment;
    char field[WR_VPN_CONFIG_MAX+64],mark[64];int section=0,ok=1;
    if (!record || !out || !record->revision || !record->size || record->size>WR_VPN_CONFIG_MAX ||
        !wr_vpn_resources_make(&resources,record->id,record->protocol)) return WR_VPN_REJECTED;
    result=wr_vpn_validate(record->protocol,record->config,record->size);
    if (result!=WR_VPN_VALID) return result;
    plan=calloc(1,sizeof(*plan));text=malloc(record->size+1);
    if (!plan || !text) { free(plan);free(text);return WR_VPN_VALIDATOR_FAILED; }
    plan->resources=resources;memcpy(text,record->config,record->size);text[record->size]=0;cursor=text;
    while (ok && cursor) {
        next=strchr(cursor,'\n');if (next) *next++=0;
        line=trim_field(cursor);cursor=next;comment=strchr(line,'#');if (comment) *comment=0;
        line=trim_field(line);if (!*line) continue;
        if (!strcasecmp(line,"[Interface]")) {
            section=1;ok=append_text(plan->native,sizeof(plan->native),"[Interface]","\n");
            snprintf(mark,sizeof(mark),"FwMark = %u",resources.mark);
            if (ok) ok=append_text(plan->native,sizeof(plan->native),mark,"\n");
            continue;
        }
        if (!strcasecmp(line,"[Peer]")) { section=2;ok=append_text(plan->native,sizeof(plan->native),"[Peer]","\n");continue; }
        equal=strchr(line,'=');if (!equal) { ok=0;break; }*equal=0;
        key=trim_field(line);value=trim_field(equal+1);
        if (section==1 && !strcasecmp(key,"Address")) {
            ok=append_text(plan->addresses,sizeof(plan->addresses),value,", ");continue;
        }
        if (section==1 && !strcasecmp(key,"DNS")) {
            ok=append_text(plan->dns,sizeof(plan->dns),value,", ");continue;
        }
        if (section==1 && !strcasecmp(key,"MTU")) { plan->mtu=(unsigned int)strtoul(value,NULL,10);continue; }
        if (section==2 && !strcasecmp(key,"Endpoint") && *value!='[') {
            unsigned char address[4];char *colon=strrchr(value,':');
            if (!colon) { ok=0;break; }
            *colon=0;if (inet_pton(AF_INET,value,address)!=1) plan->hostname_endpoints=1;*colon=':';
        }
        if (snprintf(field,sizeof(field),"%s = %s",key,value)<0) { ok=0;break; }
        ok=append_text(plan->native,sizeof(plan->native),field,"\n");
    }
    if (ok) {
        size_t n=strlen(plan->native);
        if (n+2>sizeof(plan->native)) ok=0;
        else { plan->native[n]='\n';plan->native[n+1]=0; }
    }
    if (ok) *out=*plan;
    erase(plan,sizeof(*plan));erase(text,record->size+1);erase(field,sizeof(field));free(plan);free(text);
    return ok?WR_VPN_VALID:WR_VPN_REJECTED;
}
