#include "dns-apply.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static struct wr_vpn_config_plan plan;
static char path[512];

static void prepare(const char *dns)
{
    memset(&plan,0,sizeof(plan));
    plan.resources.id=2;plan.resources.protocol=WR_VPN_WIREGUARD;
    snprintf(plan.resources.dns,sizeof(plan.resources.dns),"wrv2.dns");
    snprintf(plan.dns,sizeof(plan.dns),"%s",dns);
    snprintf(path,sizeof(path),"%s/wrv2.dns",(char *)getenv("WRTMP"));
}

int main(void)
{
    char root[]="/tmp/wrvpn-dns-XXXXXX",contents[128];struct stat st;FILE *file;size_t n;
    assert(mkdtemp(root));
    setenv("WRTMP",root,1);

    prepare("1.1.1.1, 8.8.8.8");
    assert(wr_vpn_dns_write(&plan,root)==WR_VPN_DNS_DONE);
    assert(!stat(path,&st) && (st.st_mode&0777)==0600 && st.st_nlink==1);
    file=fopen(path,"r");assert(file);
    n=fread(contents,1,sizeof(contents)-1,file);contents[n]=0;fclose(file);
    assert(!strcmp(contents,"1.1.1.1\n8.8.8.8\n"));

    prepare("2001:4860:4860::8888");
    assert(wr_vpn_dns_write(&plan,root)==WR_VPN_DNS_DONE);
    file=fopen(path,"r");assert(file);
    n=fread(contents,1,sizeof(contents)-1,file);contents[n]=0;fclose(file);
    assert(!strcmp(contents,"2001:4860:4860::8888\n"));

    prepare("");
    assert(wr_vpn_dns_write(&plan,root)==WR_VPN_DNS_EMPTY);

    prepare("1.1.1.1, not-an-address");
    assert(wr_vpn_dns_write(&plan,root)==WR_VPN_DNS_INVALID);
    file=fopen(path,"r");assert(file);
    n=fread(contents,1,sizeof(contents)-1,file);contents[n]=0;fclose(file);
    assert(!strcmp(contents,"2001:4860:4860::8888\n"));

    prepare("1.1.1.1");
    assert(wr_vpn_dns_write(&plan,"/nonexistent-wrvpn-dir")==WR_VPN_DNS_IO);

    unlink(path);rmdir(root);
    puts("PASS VPN DNS write: validated entries, IPv6, atomic 0600 file, empty and "
         "invalid cases leave the previous file untouched");
    return 0;
}
