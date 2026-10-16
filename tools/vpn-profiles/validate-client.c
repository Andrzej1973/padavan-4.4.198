/* Compile separately against the pinned WG and AWG config.c/encoding.c APIs.
 * Syntax validation only: no IPC, shell, routes, DNS queries or key output.
 * Quick fields are validated here; native protocol fields use upstream code.
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include "config.h"
#include "containers.h"

#define INPUT_MAX 16384u
static char *trim(char *s)
{
    size_t n;
    while (*s==' ' || *s=='\t') ++s;
    n=strlen(s); while (n && (s[n-1]==' ' || s[n-1]=='\t')) s[--n]=0;
    return s;
}
static int number(const char *s,unsigned int max,int zero)
{
    unsigned int n=0;
    if (!*s) return 0;
    for (;*s;s++) {
        if (*s<'0' || *s>'9' || n>max/10u) return 0;
        n=n*10u+(unsigned int)(*s-'0'); if (n>max) return 0;
    }
    return zero || n>0;
}
static int ip(const char *s)
{ unsigned char addr[16]; return inet_pton(AF_INET,s,addr)==1 || inet_pton(AF_INET6,s,addr)==1; }
static int hostname(const char *s)
{
    size_t n=strlen(s),i;
    if (!n || n>253) return 0;
    for (i=0;i<n;i++) if (!((s[i]>='a' && s[i]<='z') || (s[i]>='A' && s[i]<='Z') ||
        (s[i]>='0' && s[i]<='9') || s[i]=='-' || s[i]=='_' || s[i]=='.')) return 0;
    return 1;
}
static int address_list(char *s,int dns)
{
    char *word,*save=NULL,*slash; unsigned int count=0;
    /* Empty comma-separated entries are invalid, whitespace alone separates. */
    char *p=s; int after_comma=0,have_word=0;
    for (;*p;p++) {
        if (*p==',') { if (!have_word || after_comma) return 0; after_comma=1; have_word=0; }
        else if (*p!=' ' && *p!='\t') { have_word=1; after_comma=0; }
    }
    if (after_comma) return 0;
    for (word=strtok_r(s,", \t",&save);word;word=strtok_r(NULL,", \t",&save)) {
        if (++count>64) return 0;
        slash=strchr(word,'/');
        if (slash) {
            if (dns) return 0;
            *slash++=0;
            if (!number(slash,strchr(word,':')?128:32,1)) return 0;
        }
        if (!ip(word) && !(dns && hostname(word))) return 0;
    }
    return count>0;
}
static int endpoint(char *s)
{
    char *port,*close; unsigned char addr[16];
    if (*s=='[') {
        close=strchr(s,']'); if (!close || close[1]!=':') return 0;
        *close=0; port=close+2;
        if (inet_pton(AF_INET6,s+1,addr)!=1) return 0;
    } else {
        port=strrchr(s,':'); if (!port) return 0; *port++=0;
        if (!hostname(s) || strchr(s,':')) return 0;
    }
    return number(port,65535,0);
}
int main(void)
{
    char input[INPUT_MAX+2],native[INPUT_MAX+64],copy[INPUT_MAX+2];
    char *cursor,*next,*line,*comment,*equal,*key,*value;
    size_t n,i; int section=0,interfaces=0,private_keys=0,addresses=0,peers=0;
    int endpoint_seen=0,public_seen=0,port_seen=0,mtu_seen=0;
    struct config_ctx ctx;
    struct wgdevice *device;
    struct wgpeer *peer,*other;
    const unsigned char zero[WG_KEY_LEN]={0};
    /* Native parser diagnostics may contain an input line; never emit keys. */
    if (!freopen("/dev/null","w",stderr)) return 2;
    memset(&ctx,0,sizeof(ctx));
    n=fread(input,1,INPUT_MAX+1,stdin);
    if (ferror(stdin) || !n || n>INPUT_MAX || memchr(input,0,n)) return 2;
    for (i=0;i<n;i++) if (((unsigned char)input[i]<32 && input[i]!='\r' && input[i]!='\n' && input[i]!='\t') || input[i]==127) return 2;
    input[n]=0;
    if (!config_read_init(&ctx,false)) return 2;
    cursor=input;
    while (cursor) {
        next=strchr(cursor,'\n'); if (next) *next++=0;
        n=strlen(cursor); if (n && cursor[n-1]=='\r') cursor[n-1]=0;
        if (strchr(cursor,'\r')) goto invalid;
        comment=strchr(cursor,'#'); if (comment) *comment=0;
        line=trim(cursor); cursor=next; if (!*line) continue;
        if (!strcasecmp(line,"[Interface]")) {
            if (++interfaces!=1 || section) goto invalid;
            section=1;
        } else if (!strcasecmp(line,"[Peer]")) {
            if (!interfaces || ++peers>64) goto invalid;
            section=2; endpoint_seen=0; public_seen=0;
        } else {
            if (!section || !(equal=strchr(line,'='))) goto invalid;
            *equal=0; key=trim(line); value=trim(equal+1); if (!*value) goto invalid;
            for (i=0;key[i];i++) if (!((key[i]>='a' && key[i]<='z') ||
                (key[i]>='A' && key[i]<='Z') || (key[i]>='0' && key[i]<='9'))) goto invalid;
            if (!strcasecmp(key,"Address") || !strcasecmp(key,"DNS")) {
                if (section!=1) goto invalid;
                strcpy(copy,value); if (!address_list(copy,!strcasecmp(key,"DNS"))) goto invalid;
                if (!strcasecmp(key,"Address")) addresses++;
                continue;
            }
            if (!strcasecmp(key,"MTU")) {
                if (section!=1 || mtu_seen++ || !number(value,65535,0)) goto invalid;
                continue;
            }
            /* These change global policy or execute code, so require explicit
             * manager settings rather than imported wg-quick side effects. */
            if (!strcasecmp(key,"PreUp") || !strcasecmp(key,"PostUp") ||
                !strcasecmp(key,"PreDown") || !strcasecmp(key,"PostDown") ||
                !strcasecmp(key,"SaveConfig") || !strcasecmp(key,"Table") ||
                !strcasecmp(key,"FwMark")) goto invalid;
            if (!strcasecmp(key,"PrivateKey") && (section!=1 || private_keys++)) goto invalid;
            if (!strcasecmp(key,"PublicKey") && (section!=2 || public_seen++)) goto invalid;
            if (!strcasecmp(key,"ListenPort") && (section!=1 || port_seen++ || !number(value,65535,1))) goto invalid;
            if (!strcasecmp(key,"Endpoint")) {
                if (section!=2 || endpoint_seen++) goto invalid;
                strcpy(copy,value); if (!endpoint(copy)) goto invalid;
                /* Validate original syntax, defer DNS to activation. The
                 * native parser gets a numeric placeholder and cannot query. */
                value="127.0.0.1:51820";
            }
            if (snprintf(native,sizeof(native),"%s=%s",key,value)<0) goto invalid;
            line=native;
        }
        if (!config_read_line(&ctx,line)) { ctx.device=NULL; goto invalid; }
    }
    if (interfaces!=1 || private_keys!=1 || !addresses || !peers) goto invalid;
    device=config_read_finish(&ctx); ctx.device=NULL;
    if (!device) return 2;
    if (!memcmp(device->private_key,zero,WG_KEY_LEN)) { free_wgdevice(device); return 2; }
    for_each_wgpeer(device,peer) {
        if (!peer->first_allowedip || !memcmp(peer->public_key,zero,WG_KEY_LEN)) { free_wgdevice(device); return 2; }
        for (other=peer->next_peer;other;other=other->next_peer)
            if (!memcmp(peer->public_key,other->public_key,WG_KEY_LEN)) { free_wgdevice(device); return 2; }
    }
    free_wgdevice(device);
    puts("valid client configuration; connectivity unverified"); return 0;
invalid:
    if (ctx.device) free_wgdevice(ctx.device);
    return 2;
}
