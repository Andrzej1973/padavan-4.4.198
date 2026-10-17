#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "endpoint-pin.h"
#include <arpa/inet.h>
#include <ctype.h>
#include <string.h>

static int blank(char c)
{
    return c==' ' || c=='\t' || c=='\r';
}

/* Returns the value length when the line is an Endpoint setting, else 0. */
static int endpoint_value(const char *line,size_t length,size_t *value)
{
    static const char key[]="endpoint";
    size_t i=0,k=0;
    while (i<length && blank(line[i])) i++;
    while (i+k<length && k<sizeof(key)-1 &&
           tolower((unsigned char)line[i+k])==key[k]) k++;
    if (k!=sizeof(key)-1) return 0;
    i+=k;
    while (i<length && blank(line[i])) i++;
    if (i>=length || line[i]!='=') return 0;
    i++;
    while (i<length && blank(line[i])) i++;
    while (length>i && blank(line[length-1])) length--;
    if (length<=i) return 0;
    *value=i;
    return (int)(length-i);
}

static int numeric(const char *host,size_t length)
{
    char text[64];struct in_addr v4;struct in6_addr v6;
    if (!length || length>=sizeof(text)) return 0;
    memcpy(text,host,length);text[length]=0;
    return inet_pton(AF_INET,text,&v4)==1 || inet_pton(AF_INET6,text,&v6)==1;
}

enum wr_vpn_pin_result wr_vpn_pin_endpoints(const struct wr_vpn_record *input,
    wr_vpn_resolver resolve,struct wr_vpn_record *output)
{
    const char *text;size_t at=0,used=0;int changed=0;
    if (!input || !output || !resolve) return WR_VPN_PIN_REJECTED;
    if (!input->size || input->size>WR_VPN_CONFIG_MAX) return WR_VPN_PIN_REJECTED;
    memset(output,0,sizeof(*output));
    output->id=input->id;output->protocol=input->protocol;output->revision=input->revision;
    text=(const char *)input->config;
    while (at<input->size) {
        const char *line=text+at;
        const char *nl=memchr(line,'\n',input->size-at);
        size_t length=nl?(size_t)(nl-line):(input->size-at);
        const char *emit_line=line;size_t emit_length=length;
        char rebuilt[320];size_t value=0;int value_length=endpoint_value(line,length,&value);
        if (value_length>0) {
            const char *v=line+value;size_t n=(size_t)value_length;
            size_t host_at=0,host_length=0,port_at=0,port_length=0;
            char host[128],answer[64];int rebuilt_length,v6;
            if (v[0]=='[') {
                const char *close=memchr(v,']',n);
                if (!close || close+1>=v+n || close[1]!=':') return WR_VPN_PIN_REJECTED;
                host_at=1;host_length=(size_t)(close-(v+1));
                port_at=host_length+3;port_length=n-port_at;
            } else {
                const char *colon=memrchr(v,':',n);
                if (!colon || colon==v) return WR_VPN_PIN_REJECTED;
                host_length=(size_t)(colon-v);port_at=host_length+1;port_length=n-port_at;
            }
            if (!host_length || !port_length) return WR_VPN_PIN_REJECTED;
            if (!numeric(v+host_at,host_length)) {
                if (host_length>=sizeof(host)) return WR_VPN_PIN_REJECTED;
                memcpy(host,v+host_at,host_length);host[host_length]=0;
                if (!resolve(host,answer,sizeof(answer))) return WR_VPN_PIN_UNRESOLVED;
                v6=strchr(answer,':')!=NULL;
                rebuilt_length=v6?
                    snprintf(rebuilt,sizeof(rebuilt),"%.*s[%s]:%.*s",(int)(v-line),line,
                             answer,(int)port_length,v+port_at):
                    snprintf(rebuilt,sizeof(rebuilt),"%.*s%s:%.*s",(int)(v-line),line,
                             answer,(int)port_length,v+port_at);
                if (rebuilt_length<0 || (size_t)rebuilt_length>=sizeof(rebuilt))
                    return WR_VPN_PIN_REJECTED;
                emit_line=rebuilt;emit_length=(size_t)rebuilt_length;changed=1;
            }
        }
        if (used+emit_length+(nl?1:0)>WR_VPN_CONFIG_MAX) return WR_VPN_PIN_TOO_LONG;
        memcpy((char *)output->config+used,emit_line,emit_length);used+=emit_length;
        if (nl) ((char *)output->config)[used++]='\n';
        at+=length+(nl?1:0);
    }
    output->size=used;
    return changed?WR_VPN_PIN_DONE:WR_VPN_PIN_UNCHANGED;
}
