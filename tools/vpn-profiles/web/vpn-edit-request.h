#ifndef WR_VPN_EDIT_REQUEST_H
#define WR_VPN_EDIT_REQUEST_H
#include <stdint.h>
#include "vpn-create-request.h"
#define WR_VPN_EDIT_BODY_MAX (WR_VPN_CREATE_CONFIG_MAX+96u)
struct wr_vpn_edit_request {
    char token[33];
    unsigned int id;
    uint64_t revision;
    const unsigned char *config;
    size_t size;
};
/* Token LF canonical ID LF canonical expected revision LF private config. */
static inline int wr_vpn_edit_parse(const unsigned char *body,size_t size,
                                   struct wr_vpn_edit_request *out)
{
    struct wr_vpn_edit_request value;
    size_t i,pos=33,begin;
    if (!body || !out || size<38 || size>WR_VPN_EDIT_BODY_MAX || memchr(body,0,size)) return 0;
    memset(&value,0,sizeof(value));
    for(i=0;i<32;i++) {
        unsigned char c=body[i];
        if (!((c>='0'&&c<='9')||(c>='a'&&c<='f'))) return 0;
        value.token[i]=(char)c;
    }
    if(body[32]!='\n' || body[pos]<'1' || body[pos]>'9') return 0;
    begin=pos;
    while(pos<size && body[pos]!='\n') {
        if(pos-begin>=3 || body[pos]<'0' || body[pos]>'9') return 0;
        value.id=value.id*10u+(unsigned int)(body[pos++]-'0');
    }
    if(pos>=size || !value.id || value.id>999) return 0;
    if(++pos>=size || body[pos]<'1' || body[pos]>'9') return 0;
    while(pos<size && body[pos]!='\n') {
        unsigned int digit=(unsigned int)(body[pos++]-'0');
        if(digit>9 || value.revision>(UINT64_MAX-digit)/10) return 0;
        value.revision=value.revision*10+digit;
    }
    if(pos>=size || !value.revision || value.revision==UINT64_MAX) return 0;
    value.config=body+pos+1;value.size=size-pos-1;
    if(!value.size || value.size>WR_VPN_CREATE_CONFIG_MAX) return 0;
    *out=value;return 1;
}
#endif
