#!/usr/bin/env python3
"""Host test for the authenticated profile action endpoint with stubs."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--work", type=Path, help="pre-created work directory (Windows local runs)")
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
here = Path(__file__).resolve().parent

PREFIX = r'''
#include <assert.h>
#include <fcntl.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
typedef FILE *webs_t;
static int safe, post, posted, parsed;
static char reply[4096];
static char req_token[40], req_ack[4] = "1", req_op[16] = "up", req_id[8] = "1", req_protect[64] = "192.168.20.0/24";
static int websWrite(webs_t wp, const char *format, ...)
{va_list ap;int n;(void)wp;va_start(ap,format);n=vsnprintf(reply,sizeof(reply),format,ap);va_end(ap);return n;}
static int get_login_safe(void){return safe;}
int wr_vpn_request_is_post(void){return post;}
static char *websGetVar(webs_t wp, const char *key, const char *fallback)
{
 (void)wp;
 if(!strcmp(key,"token"))return req_token;
 if(!strcmp(key,"ack"))return req_ack;
 if(!strcmp(key,"operation"))return req_op;
 if(!strcmp(key,"id"))return req_id;
 if(!strcmp(key,"protect"))return req_protect;
 return (char *)fallback;
}
static void init_cgi(char *p){(void)p;}
static void do_html_apply_post(const char *u,FILE *f,int c,char *b){(void)u;(void)f;(void)c;(void)b;parsed++;}
'''

TESTS = r'''
static void submit(void){wr_vpn_post_seen=1;wr_vpn_action_output("",NULL);}
int main(int argc,char **argv)
{
 char *state_args[] = {"1"};
 int fd;char path[256];
 if(argc!=2)return 99;
 (void)argv;
 wr_vpn_action_input("",NULL,1,NULL);assert(wr_vpn_post_seen);
 ej_wr_vpn_token(0,NULL,0,NULL);assert(!strcmp(reply,"\"\""));
 safe=1;ej_wr_vpn_token(0,NULL,0,NULL);assert(strlen(wr_vpn_csrf)==32);
 strcpy(req_token,wr_vpn_csrf);
 submit();assert(strstr(reply,"unsafe_request"));
 posted=1;post=1;
 strcpy(req_token,"bad");submit();assert(strstr(reply,"invalid_token"));
 strcpy(req_token,wr_vpn_csrf);strcpy(req_ack,"0");submit();assert(strstr(reply,"confirmation"));strcpy(req_ack,"1");
 strcpy(req_op,"frobnicate");submit();assert(strstr(reply,"invalid_request"));strcpy(req_op,"up");
 strcpy(req_id,"0");submit();assert(strstr(reply,"invalid_request"));
 strcpy(req_id,"1000");submit();assert(strstr(reply,"invalid_request"));
 strcpy(req_id,"1x");submit();assert(strstr(reply,"invalid_request"));strcpy(req_id,"1");
 strcpy(req_protect,"bad;cmd");submit();assert(strstr(reply,"invalid_request"));strcpy(req_protect,"192.168.20.0/24");
 wr_vpn_worker=getpid();submit();assert(strstr(reply,"busy"));wr_vpn_worker=0;
 submit();assert(strstr(reply,"accepted"));
 {int i;for(i=0;i<50;i++){usleep(20000);if(wr_vpn_reap())break;}}
 snprintf(path,sizeof(path),"%s/args",getenv("WRVPN_TEST_DIR"));
 fd=open(path,O_RDONLY);assert(fd>=0);
 {char text[128];ssize_t n=read(fd,text,sizeof(text)-1);close(fd);text[n>0?n:0]=0;
  assert(!strcmp(text,"1 up 192.168.20.0/24\n"));}
 snprintf(path,sizeof(path),"%s/1",getenv("WRVPN_TEST_STATE"));
 fd=open(path,O_WRONLY|O_CREAT|O_TRUNC,0600);assert(fd>=0);
 {const char *text="state=done\ncode=0\noutput=up 1 ok\n";write(fd,text,strlen(text));}
 close(fd);
 ej_wr_vpn_action_state(0,NULL,1,state_args);assert(strstr(reply,"\"state\":\"done\"")&&strstr(reply,"\"code\":0"));
 puts("PASS VPN action endpoint: CSRF, ack, id/operation/protect guards, busy, exact worker argv and state read");
 return 0;
}
'''


def checks(root: Path) -> None:
    worker = root / "worker"
    worker.write_text('#!/bin/sh\nprintf "%s\\n" "$*" > "%s/args"\n' % ("%s", root))
    worker.chmod(0o700)
    state_dir = root / "state"
    state_dir.mkdir()
    harness = root / "harness.c"
    harness.write_text(PREFIX + '#include "vpn-profiles-action.inc"\n' + TESTS)
    exe = root / "check"
    subprocess.run(
        [
            "gcc", "-std=gnu99", "-Wall", "-Wextra", "-Werror", "-g",
            "-fsanitize=address,undefined",
            "-I" + str(here / "web"),
            '-DWR_VPN_ACTION_WORKER="%s"' % worker,
            '-DWR_VPN_ACTION_STATE_ROOT="%s"' % state_dir,
            str(harness), "-o", str(exe),
        ],
        check=True,
    )
    env = dict(os.environ, WRVPN_TEST_DIR=str(root), WRVPN_TEST_STATE=str(state_dir),
               ASAN_OPTIONS="detect_leaks=1:exitcode=98",
               UBSAN_OPTIONS="halt_on_error=1:exitcode=97")
    result = subprocess.run([str(exe), "state"], capture_output=True, timeout=20, env=env)
    assert result.returncode == 0, (result.returncode, result.stderr)
    print(result.stdout.decode().strip())


if args.work:
    checks(args.work)
else:
    with tempfile.TemporaryDirectory(prefix="wrvpn-http-") as temporary:
        checks(Path(temporary))
