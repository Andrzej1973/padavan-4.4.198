#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "dns-apply.h"
#include <arpa/inet.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

static int valid_address(const char *text,size_t length)
{
    char buffer[64];struct in_addr v4;struct in6_addr v6;
    if (!length || length>=sizeof(buffer)) return 0;
    memcpy(buffer,text,length);buffer[length]=0;
    return inet_pton(AF_INET,buffer,&v4)==1 || inet_pton(AF_INET6,buffer,&v6)==1;
}

enum wr_vpn_dns_result wr_vpn_dns_write(const struct wr_vpn_config_plan *plan,
                                        const char *directory)
{
    const char *cursor;char path[512],temp[540];char line[72];
    int fd,written=0;
    if (!plan || !directory || !*directory) return WR_VPN_DNS_INVALID;
    if (!plan->dns[0]) return WR_VPN_DNS_EMPTY;
    if (snprintf(path,sizeof(path),"%s/%s",directory,plan->resources.dns)<0) return WR_VPN_DNS_INVALID;
    if (snprintf(temp,sizeof(temp),"%s/.dns-%ld",directory,(long)getpid())<0) return WR_VPN_DNS_IO;

    /* Validate every entry before creating anything. */
    for (cursor=plan->dns; cursor && *cursor; ) {
        const char *comma=strstr(cursor,", ");
        size_t length=comma?(size_t)(comma-cursor):strlen(cursor);
        while (length && *cursor==' ') { cursor++;length--; }
        while (length && cursor[length-1]==' ') length--;
        if (!valid_address(cursor,length)) return WR_VPN_DNS_INVALID;
        cursor=comma?comma+2:NULL;
    }

    fd=open(temp,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if (fd<0) return WR_VPN_DNS_IO;
    for (cursor=plan->dns; cursor && *cursor; ) {
        const char *comma=strstr(cursor,", ");
        size_t length=comma?(size_t)(comma-cursor):strlen(cursor);
        int n;
        while (length && *cursor==' ') { cursor++;length--; }
        while (length && cursor[length-1]==' ') length--;
        n=snprintf(line,sizeof(line),"%.*s\n",(int)length,cursor);
        if (n<0 || write(fd,line,(size_t)n)!=n) {
            close(fd);unlink(temp);return WR_VPN_DNS_IO;
        }
        written=1;
        cursor=comma?comma+2:NULL;
    }
    if (close(fd) || !written) { unlink(temp);return WR_VPN_DNS_IO; }
    if (rename(temp,path)) { unlink(temp);return WR_VPN_DNS_IO; }
    return WR_VPN_DNS_DONE;
}
