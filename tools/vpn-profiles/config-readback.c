/* Compile against each pinned native parser and IPC implementation. Read-only:
 * stdin is a validated numeric-endpoint config-plan payload, argv is the owned
 * canonical interface and recorded index. Parent must bound execution, suppress
 * diagnostics and check session/link identity before and after this snapshot.
 * Exit 0: requested protocol configuration matches; 2: mismatch; 3: unknown.
 * This does not verify address/route/DNS policy, handshake or connectivity.
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <arpa/inet.h>
#include <netdb.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include "config.h"
#include "containers.h"
#include "ipc.h"
#include "resources.h"

/* Link with --wrap=getaddrinfo: even malformed input cannot trigger DNS. */
int __real_getaddrinfo(const char *,const char *,const struct addrinfo *,struct addrinfo **);
int __wrap_getaddrinfo(const char *node,const char *service,const struct addrinfo *hints,struct addrinfo **out)
{
    struct addrinfo h={0};if (hints) h=*hints;
    h.ai_flags |= AI_NUMERICHOST|AI_NUMERICSERV;
    return __real_getaddrinfo(node,service,&h,out);
}
static int subnet_equal(const struct wgallowedip *a,const struct wgallowedip *b)
{
    unsigned int i,bits=a->cidr,max;const unsigned char *x,*y;
    if (a->family!=b->family || a->cidr!=b->cidr) return 0;
    if (a->family==AF_INET) { max=32;x=(const void *)&a->ip4;y=(const void *)&b->ip4; }
    else if (a->family==AF_INET6) { max=128;x=(const void *)&a->ip6;y=(const void *)&b->ip6; }
    else return 0;
    if (bits>max) return 0;
    for (i=0;bits>=8;i++,bits-=8) if (x[i]!=y[i]) return 0;
    return !bits || ((x[i]^y[i]) & (0xffu << (8-bits)))==0;
}
static int subnets_contained(const struct wgpeer *a,const struct wgpeer *b)
{
    const struct wgallowedip *x,*y;
    for (x=a->first_allowedip;x;x=x->next_allowedip) {
        for (y=b->first_allowedip;y;y=y->next_allowedip) if (subnet_equal(x,y)) break;
        if (!y) return 0;
    }
    return 1;
}
static int endpoint_equal(const struct wgpeer *a,const struct wgpeer *b)
{
    if (!a->endpoint.addr.sa_family) return 1; /* roaming endpoint not specified */
    if (a->endpoint.addr.sa_family!=b->endpoint.addr.sa_family) return 0;
    if (a->endpoint.addr.sa_family==AF_INET)
        return a->endpoint.addr4.sin_port==b->endpoint.addr4.sin_port &&
            !memcmp(&a->endpoint.addr4.sin_addr,&b->endpoint.addr4.sin_addr,4);
    if (a->endpoint.addr.sa_family==AF_INET6)
        return a->endpoint.addr6.sin6_port==b->endpoint.addr6.sin6_port &&
            a->endpoint.addr6.sin6_scope_id==b->endpoint.addr6.sin6_scope_id &&
            !memcmp(&a->endpoint.addr6.sin6_addr,&b->endpoint.addr6.sin6_addr,16);
    return 0;
}
static int matches(const struct wgdevice *want,const struct wgdevice *have)
{
    const struct wgpeer *p,*q,*duplicate;unsigned int count=0,actual=0;
    if (memcmp(want->private_key,have->private_key,WG_KEY_LEN) || want->fwmark!=have->fwmark) return 0;
    /* Zero/omitted ListenPort asks the kernel to allocate a port. */
    if (want->listen_port && want->listen_port!=have->listen_port) return 0;
#ifdef WR_VPN_NATIVE_AWG
#define FIELD(flag,field) if ((want->flags & (flag)) && (!(have->flags & (flag)) || want->field!=have->field)) return 0
    FIELD(WGDEVICE_HAS_JC,junk_packet_count);
    FIELD(WGDEVICE_HAS_JMIN,junk_packet_min_size);
    FIELD(WGDEVICE_HAS_JMAX,junk_packet_max_size);
    FIELD(WGDEVICE_HAS_S1,init_packet_junk_size);
    FIELD(WGDEVICE_HAS_S2,response_packet_junk_size);
    FIELD(WGDEVICE_HAS_S3,cookie_reply_packet_junk_size);
    FIELD(WGDEVICE_HAS_S4,transport_packet_junk_size);
    FIELD(WGDEVICE_HAS_H1,init_header);FIELD(WGDEVICE_HAS_H2,resp_header);
    FIELD(WGDEVICE_HAS_H3,cookie_header);FIELD(WGDEVICE_HAS_H4,transport_header);
    FIELD(WGDEVICE_HAS_CONTENT_PADDING_ADDITION,content_padding_addition);
    FIELD(WGDEVICE_HAS_REKEY_AFTER_TIME,rekey_after_time);
    FIELD(WGDEVICE_HAS_REKEY_TIMEOUT,rekey_timeout);
    FIELD(WGDEVICE_HAS_REJECT_AFTER_TIME,reject_after_time);
    FIELD(WGDEVICE_HAS_KEEPALIVE_TIMEOUT,keepalive_timeout);
    FIELD(WGDEVICE_HAS_MAX_HANDSHAKE_ATTEMPTS,max_handshake_attempts);
    FIELD(WGDEVICE_HAS_RANDOM_TRAILERS,random_trailers);
    FIELD(WGDEVICE_HAS_DISABLE_COOKIES,disable_cookies);
#undef FIELD
#define STRING_FIELD(flag,field) if ((want->flags & (flag)) && (!(have->flags & (flag)) || !want->field || !have->field || strcmp(want->field,have->field))) return 0
    STRING_FIELD(WGDEVICE_HAS_I1,i1);STRING_FIELD(WGDEVICE_HAS_I2,i2);
    STRING_FIELD(WGDEVICE_HAS_I3,i3);STRING_FIELD(WGDEVICE_HAS_I4,i4);STRING_FIELD(WGDEVICE_HAS_I5,i5);
#undef STRING_FIELD
    if ((want->flags & WGDEVICE_HAS_HEADER_PROTECTION_KEY) &&
        (!(have->flags & WGDEVICE_HAS_HEADER_PROTECTION_KEY) ||
         memcmp(want->header_protection_key,have->header_protection_key,WG_KEY_LEN))) return 0;
#endif
    for (p=want->first_peer;p;p=p->next_peer) {
        if (++count>64) return 0;
        for (duplicate=p->next_peer;duplicate;duplicate=duplicate->next_peer)
            if (!memcmp(p->public_key,duplicate->public_key,WG_KEY_LEN)) return 0;
        for (q=have->first_peer;q;q=q->next_peer) if (!memcmp(p->public_key,q->public_key,WG_KEY_LEN)) break;
        if (!q || memcmp(p->preshared_key,q->preshared_key,WG_KEY_LEN) ||
            p->persistent_keepalive_interval!=q->persistent_keepalive_interval ||
            !endpoint_equal(p,q) || !subnets_contained(p,q) || !subnets_contained(q,p)) return 0;
#ifdef WR_VPN_NATIVE_AWG
        if ((p->flags & WGPEER_HAS_AWG) && (!(q->flags & WGPEER_HAS_AWG) || p->awg!=q->awg)) return 0;
#endif
    }
    for (q=have->first_peer;q;q=q->next_peer) if (++actual>64) return 0;
    return count && count==actual;
}
int main(int argc,char **argv)
{
    char input[33000],*line,*next;size_t n;unsigned int id;uint64_t index=0;
    const char *digit;struct config_ctx ctx={0};struct wgdevice *want=NULL,*have=NULL;
    struct rlimit core={0,0};int result=3;
    if (setrlimit(RLIMIT_CORE,&core) || !freopen("/dev/null","w",stderr)) return 3;
    if (argc!=3 || strncmp(argv[1],"wrvpn",5) || !wr_vpn_profile_id(argv[1]+5,&id) || !*argv[2]) return 3;
    for (digit=argv[2];*digit;digit++) {
        if (*digit<'0' || *digit>'9') return 3;
        index=index*10+(unsigned int)(*digit-'0');if (index>UINT32_MAX) return 3;
    }
    if (!index) return 3;
    n=fread(input,1,sizeof(input),stdin);
    if (ferror(stdin) || !n || n==sizeof(input) || memchr(input,0,n)) return 3;
    input[n]=0;if (!config_read_init(&ctx,false)) return 3;
    for (line=input;line;line=next) {
        next=strchr(line,'\n');if (next) *next++=0;
        if (!config_read_line(&ctx,line)) return 3; /* parser frees on failure */
    }
    want=config_read_finish(&ctx);if (!want) return 3;
    if (!(want->flags & WGDEVICE_HAS_PRIVATE_KEY) || !(want->flags & WGDEVICE_HAS_FWMARK)) goto finish;
    if (ipc_get_device(&have,argv[1]) || !have) goto finish;
    if (have->ifindex!=index || strcmp(have->name,argv[1])) goto finish;
    result=matches(want,have)?0:2;
finish:
    free_wgdevice(want);free_wgdevice(have);return result;
}
