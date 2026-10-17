#ifndef WR_VPN_CREATE_REQUEST_H
#define WR_VPN_CREATE_REQUEST_H
#include <stddef.h>
#include <string.h>

#define WR_VPN_CREATE_CONFIG_MAX 16384u
#define WR_VPN_CREATE_BODY_MAX (WR_VPN_CREATE_CONFIG_MAX + 64u)
struct wr_vpn_create_request {
    char token[33];
    unsigned int id;
    const char *protocol;
    const unsigned char *config;
    size_t size;
};

/* Wire format: lowercase hex token LF canonical numeric ID LF protocol LF
 * config bytes. This parses data only; caller must authenticate POST, compare
 * CSRF token, then use the native validator before creating a private record.
 * Config borrows the request buffer and must never enter argv or a log. */
static inline int wr_vpn_create_parse(const unsigned char *body,size_t size,
                                      struct wr_vpn_create_request *out)
{
    struct wr_vpn_create_request value;
    size_t pos,i,begin;
    unsigned int id=0;
    if (!body || !out || size<38 || size>WR_VPN_CREATE_BODY_MAX ||
        memchr(body,0,size)) return 0;
    memset(&value,0,sizeof(value));
    for (i=0;i<32;i++) {
        unsigned char c=body[i];
        if (!((c>='0'&&c<='9')||(c>='a'&&c<='f'))) return 0;
        value.token[i]=(char)c;
    }
    if (body[32]!='\n') return 0;
    pos=33;begin=pos;
    if (body[pos]<'1'||body[pos]>'9') return 0;
    while (pos<size && body[pos]!='\n') {
        if (pos-begin>=3 || body[pos]<'0'||body[pos]>'9') return 0;
        id=id*10u+(unsigned int)(body[pos++]-'0');
    }
    if (pos>=size || !id || id>999) return 0;
    value.id=id;begin=++pos;
    while (pos<size && body[pos]!='\n') ++pos;
    if (pos>=size) return 0;
    if (pos-begin==9 && !memcmp(body+begin,"wireguard",9))
        value.protocol="wireguard";
    else if (pos-begin==9 && !memcmp(body+begin,"amneziawg",9))
        value.protocol="amneziawg";
    else return 0;
    value.config=body+pos+1;value.size=size-pos-1;
    if (!value.size || value.size>WR_VPN_CREATE_CONFIG_MAX) return 0;
    *out=value;
    return 1;
}
#endif
