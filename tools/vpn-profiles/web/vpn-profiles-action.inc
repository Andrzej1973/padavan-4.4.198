/* Authenticated POST actions for stored profiles. The HTTP process only
 * starts the detached worker and reads its result; it never waits for a
 * tunnel operation. */
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#ifndef WR_VPN_ACTION_WORKER
#define WR_VPN_ACTION_WORKER "/usr/libexec/wrvpn/action-worker"
#endif
#ifndef WR_VPN_ACTION_STATE_ROOT
#define WR_VPN_ACTION_STATE_ROOT "/var/run/wrvpn/actions"
#endif

static char wr_vpn_csrf[33];
static int wr_vpn_post_seen;
static pid_t wr_vpn_worker;
extern int wr_vpn_request_is_post(void);

static int ej_wr_vpn_token(int eid,webs_t wp,int argc,char **argv)
{
    int fd,i;ssize_t got;unsigned char random[16];
    (void)eid;(void)argv;
    if (argc || !get_login_safe()) return websWrite(wp,"\"\"");
    if (!wr_vpn_csrf[0]) {
        fd=open("/dev/urandom",O_RDONLY);
        if (fd<0) return websWrite(wp,"\"\"");
        got=read(fd,random,sizeof(random));close(fd);
        if (got!=(ssize_t)sizeof(random)) return websWrite(wp,"\"\"");
        for (i=0;i<16;i++) snprintf(wr_vpn_csrf+i*2,3,"%02x",random[i]);
    }
    return websWrite(wp,"\"%s\"",wr_vpn_csrf);
}

static void wr_vpn_action_input(const char *url,FILE *stream,int clen,char *boundary)
{
    wr_vpn_post_seen=0;
    if (clen<=0 || clen>512) { while (clen-->0) if (fgetc(stream)==EOF) break; init_cgi(NULL); return; }
    do_html_apply_post(url,stream,clen,boundary);
    wr_vpn_post_seen=1;
}

static int wr_vpn_reap(void)
{
    int status;
    if (wr_vpn_worker<=0) return 1;
    if (waitpid(wr_vpn_worker,&status,WNOHANG)==wr_vpn_worker) { wr_vpn_worker=0;return 1; }
    return 0;
}

static int wr_vpn_action_id(const char *text,unsigned int *out)
{
    unsigned int value=0;const unsigned char *p=(const unsigned char *)text;
    if (!p || !out || *p<'1' || *p>'9') return 0;
    for (;*p;p++) {
        if (*p<'0' || *p>'9') return 0;
        value=value*10u+(unsigned int)(*p-'0');
        if (value>999u) return 0;
    }
    *out=value;return 1;
}

static int wr_vpn_action_protect(const char *text)
{
    size_t i,length;
    if (!text || !*text) return 1;
    length=strlen(text);
    if (length>200) return 0;
    for (i=0;i<length;i++) {
        char c=text[i];
        if (!((c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F')||
              c==':'||c=='.'||c=='/'||c==',')) return 0;
    }
    return 1;
}

static int wr_vpn_spawn(const char *id,const char *operation,const char *protect)
{
    const char *args[5];pid_t child;int fd;
    args[0]=WR_VPN_ACTION_WORKER;args[1]=id;args[2]=operation;args[3]=protect;args[4]=NULL;
    child=fork();
    if (child<0) return 0;
    if (!child) {
        fd=open("/dev/null",O_RDWR);
        if (fd>=0) { dup2(fd,0);dup2(fd,1);dup2(fd,2);if (fd>2) close(fd); }
        { int i;for (i=3;i<256;i++) close(i); }
        execv(args[0],(char *const *)args);
        _exit(127);
    }
    wr_vpn_worker=child;
    return 1;
}

static void wr_vpn_action_output(const char *url,FILE *stream)
{
    unsigned int id;int posted=wr_vpn_post_seen;
    const char *token,*operation,*idtext,*protect;
    (void)url;wr_vpn_post_seen=0;
    if (!posted || !wr_vpn_request_is_post() || !get_login_safe()) {
        websWrite(stream,"{\"error\":\"unsafe_request\"}");return;
    }
    token=websGetVar(stream,"token","");
    if (!wr_vpn_csrf[0] || strlen(token)!=32 || strcmp(token,wr_vpn_csrf) ||
        strcmp(websGetVar(stream,"ack",""),"1")) {
        websWrite(stream,"{\"error\":\"invalid_token_or_confirmation\"}");return;
    }
    operation=websGetVar(stream,"operation","");
    idtext=websGetVar(stream,"id","");
    protect=websGetVar(stream,"protect","");
    if ((strcmp(operation,"up") && strcmp(operation,"down") && strcmp(operation,"delete")) ||
        !wr_vpn_action_id(idtext,&id) || !wr_vpn_action_protect(protect)) {
        websWrite(stream,"{\"error\":\"invalid_request\"}");return;
    }
    if (!wr_vpn_reap()) { websWrite(stream,"{\"error\":\"busy\"}");return; }
    if (!wr_vpn_spawn(idtext,operation,protect)) {
        websWrite(stream,"{\"error\":\"busy_or_unavailable\"}");return;
    }
    websWrite(stream,"{\"accepted\":true,\"id\":%u}",id);
}

static int ej_wr_vpn_action_state(int eid,webs_t wp,int argc,char **argv)
{
    unsigned int id;char path[96],text[2300];struct stat st;int fd;
    ssize_t got;const char *state="unknown";int code=-1;
    (void)eid;
    if (argc!=1 || !get_login_safe()) return websWrite(wp,"{\"error\":\"unsafe_request\"}");
    if (!wr_vpn_action_id(argv[0],&id)) return websWrite(wp,"{\"error\":\"invalid_request\"}");
    snprintf(path,sizeof(path),"%s/%u",WR_VPN_ACTION_STATE_ROOT,id);
    fd=open(path,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if (fd<0) return websWrite(wp,"{\"state\":\"unknown\",\"code\":-1}");
    if (fstat(fd,&st) || !S_ISREG(st.st_mode) || st.st_size<=0 || st.st_size>=(off_t)sizeof(text)) {
        close(fd);return websWrite(wp,"{\"state\":\"unknown\",\"code\":-1}");
    }
    got=read(fd,text,(size_t)st.st_size);close(fd);
    if (got!=(ssize_t)st.st_size) return websWrite(wp,"{\"state\":\"unknown\",\"code\":-1}");
    text[got]=0;
    {
        char *code_line=strstr(text,"\ncode=");
        if (code_line) code=atoi(code_line+6);
    }
    if (!strncmp(text,"state=",6)) {
        char *end=strchr(text,'\n');
        if (end) *end=0;
        state=text+6;
        if (!strcmp(state,"running")) {
            time_t now=time(NULL);
            if (now-st.st_mtime>120) state="stale";
        }
    }
    if (strcmp(state,"done") && strcmp(state,"failed") && strcmp(state,"timeout") &&
        strcmp(state,"overflow") && strcmp(state,"running") && strcmp(state,"stale"))
        state="unknown";
    return websWrite(wp,"{\"state\":\"%s\",\"code\":%d}",state,code);
}
