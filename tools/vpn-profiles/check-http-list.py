#!/usr/bin/env python3
"""Host test for the read-only profile table with a fake manager binary."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--work", type=Path, help="pre-created work directory (Windows local runs)")
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
here = Path(__file__).resolve().parent

FAKE = '''#!/bin/sh
echo x >> "$FAKE_MARKER"
case "$FAKE_MODE" in
  ok) printf '1\\tWG1\\t2\\n2\\tAWG2\\t5\\n';;
  empty) :;;
  many) i=25; while [ "$i" -gt 0 ]; do printf '%s\\tWG%s\\t1\\n' "$i" "$i"; i=$((i-1)); done;;
  bad) printf 'garbage\\n';;
  fail) exit 3;;
  slow) sleep 2;;
  closed-output) exec 1>&- 2>&-; exec sleep 5;;
  *) exit 9;;
esac
'''

HARNESS = r'''#include <assert.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
typedef FILE *webs_t;
static int safe;
static char reply[10000];
static int websWrite(webs_t wp,const char *format,...)
{va_list ap;int n;(void)wp;va_start(ap,format);n=vsnprintf(reply,sizeof(reply),format,ap);va_end(ap);return n;}
static int get_login_safe(void){return safe;}
#include "vpn-profiles.inc"
static void run(const char *mode)
{
 reply[0]=0;setenv("FAKE_MODE",mode,1);ej_wr_vpn_profile_rows(0,NULL,0,NULL);
}
int main(int argc,char **argv)
{
 if(argc!=2)return 99;
 setenv("FAKE_MARKER",argv[1],1);
 safe=0;run("ok");assert(strstr(reply,"unavailable"));
 {FILE *f=fopen(argv[1],"r");assert(!f);}
 safe=1;run("ok");
 assert(strstr(reply,"<td>1</td><td>WG1</td><td>2</td>"));
 assert(strstr(reply,"<td>2</td><td>AWG2</td><td>5</td>"));
 run("empty");assert(strstr(reply,"none"));
 run("bad");assert(strstr(reply,"unavailable")&&!strstr(reply,"<td>1</td>"));
 run("fail");assert(strstr(reply,"unavailable"));
 run("slow");assert(strstr(reply,"unavailable"));
 {char *page="1";setenv("FAKE_MODE","many",1);ej_wr_vpn_profile_rows(0,NULL,1,&page);
  assert(strstr(reply,"<td>11</td><td>WG11</td>") && strstr(reply,"data-total=\"25\""));
  assert(!strstr(reply,"<td>1</td><td>WG1</td>") && !strstr(reply,"<td>21</td><td>WG21</td>"));
  page="99";ej_wr_vpn_profile_rows(0,NULL,1,&page);
  assert(strstr(reply,"<td>25</td><td>WG25</td>") && strstr(reply,"data-page=\"2\""));
  page="-1";ej_wr_vpn_profile_rows(0,NULL,1,&page);assert(strstr(reply,"unavailable"));}
 {long long began=wr_vpn_web_ms();run("closed-output");
  assert(strstr(reply,"unavailable") && wr_vpn_web_ms()-began<1500);}
 unlink(argv[1]);
 puts("PASS VPN profile table: login refusal, bounded rendering and timeout including closed-output live child");
 return 0;
}
'''

def checks(root: Path) -> None:
    fake = root / "fake-manager"
    fake.write_text(FAKE)
    fake.chmod(0o700)
    harness = root / "harness.c"
    harness.write_text(HARNESS)
    exe = root / "check"
    subprocess.run(
        [
            "gcc", "-std=gnu99", "-Wall", "-Wextra", "-Werror", "-g",
            "-fsanitize=address,undefined",
            "-I" + str(here / "web"),
            '-DWR_VPN_PROFILE_BIN="%s"' % fake,
            "-DWR_VPN_LIST_TIMEOUT_MS=300",
            str(harness), "-o", str(exe),
        ],
        check=True,
    )
    result = subprocess.run(
        [str(exe), str(root / "marker")],
        capture_output=True, timeout=20,
        env=dict(__import__("os").environ, ASAN_OPTIONS="detect_leaks=1:exitcode=98",
                 UBSAN_OPTIONS="halt_on_error=1:exitcode=97"),
    )
    assert result.returncode == 0, (result.returncode, result.stderr)
    print(result.stdout.decode().strip())


if args.work:
    checks(args.work)
else:
    with tempfile.TemporaryDirectory(prefix="wrvpn-web-") as temporary:
        checks(Path(temporary))
