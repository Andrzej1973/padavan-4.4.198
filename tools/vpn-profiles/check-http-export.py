#!/usr/bin/env python3
"""Host test for the authenticated profile export endpoint."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--work", type=Path, help="pre-created work directory (Windows local runs)")
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
here = Path(__file__).resolve().parent

PREFIX = r'''
#include <assert.h>
#include <fcntl.h>
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
static int safe, post;
static char reply[65536];
static char req_token[40], req_ack[4] = "1", req_id[8] = "1", req_op[8] = "up", req_protect[8] = "";
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
static void do_html_apply_post(const char *u,FILE *f,int c,char *b){(void)u;(void)f;(void)c;(void)b;}
'''

TESTS = r'''
static void submit(void){wr_vpn_post_seen=1;wr_vpn_export_output("",NULL);}
int main(void)
{
 safe=0;submit();assert(strstr(reply,"unsafe_request"));
 safe=1;post=0;submit();assert(strstr(reply,"unsafe_request"));
 post=1;strcpy(req_token,"bad");submit();assert(strstr(reply,"invalid_token"));
 ej_wr_vpn_token(0,NULL,0,NULL);strcpy(req_token,wr_vpn_csrf);
 strcpy(req_ack,"0");submit();assert(strstr(reply,"confirmation"));strcpy(req_ack,"1");
 strcpy(req_id,"0");submit();assert(strstr(reply,"invalid_request"));strcpy(req_id,"1");
 submit();assert(strstr(reply,"\"config\":\"[Interface]\\nPrivateKey = \\\"a\\\\b\\\"\\n[Peer]\\n"));
 wr_vpn_worker=0;
 puts("PASS VPN export endpoint: login/POST/CSRF guards, canonical id, JSON escaping");
 return 0;
}
'''


def checks(root: Path) -> None:
    export = root / "manager"
    export.write_text("#!/bin/sh\ncat <<'EOF'\n[Interface]\nPrivateKey = \"a\\b\"\n[Peer]\nEOF\n")
    export.chmod(0o700)
    harness = root / "harness.c"
    harness.write_text(
        PREFIX
        + '#include "vpn-profiles.inc"\n'
        + '#include "vpn-profiles-action.inc"\n'
        + '#include "vpn-profiles-export.inc"\n'
        + TESTS
    )
    exe = root / "check"
    subprocess.run(
        [
            "gcc", "-std=gnu99", "-Wall", "-Wextra", "-Werror", "-g",
            "-Wno-unused-function",
            "-fsanitize=address,undefined",
            "-I" + str(here / "web"),
            '-DWR_VPN_PROFILE_BIN="%s"' % export,
            "-DWR_VPN_LIST_TIMEOUT_MS=500",
            str(harness), "-o", str(exe),
        ],
        check=True,
    )
    result = subprocess.run(
        [str(exe)], capture_output=True, timeout=20,
        env=dict(os.environ, ASAN_OPTIONS="detect_leaks=1:exitcode=98",
                 UBSAN_OPTIONS="halt_on_error=1:exitcode=97"),
    )
    assert result.returncode == 0, (result.returncode, result.stderr)
    print(result.stdout.decode().strip())


if args.work:
    checks(args.work)
else:
    with tempfile.TemporaryDirectory(prefix="wrvpn-export-") as temporary:
        checks(Path(temporary))
