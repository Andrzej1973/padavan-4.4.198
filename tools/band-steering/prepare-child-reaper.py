"""Preserve owned steering exit status in an isolated rc tree only."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('source',type=Path)
root=p.parse_args().source; rc=root/'trunk/user/rc'
init=rc/'init.c'; make=rc/'Makefile'
text=init.read_text(); mk=make.read_text()
old='\tpid_t pid;\n\n\twhile ((pid = waitpid(-1, NULL, WNOHANG)) > 0)\n\t\tdprintf("Reaped %d\\n", pid);'
if text.count(old)!=1 or mk.count('OBJS += wr-band-profile-policy.o\n')!=1:
    raise ValueError('Prepared rc reaper/build anchors changed; no files written')
new='''\tpid_t pid;
#ifdef USE_WR_BAND_STEERING_PROFILE
\tint status;
\twhile ((pid = waitpid(-1, &status, WNOHANG)) > 0) {
\t\twr_band_child_reaped(pid, status);
\t\tdprintf("Reaped %d\\n", pid);
\t}
#else
\twhile ((pid = waitpid(-1, NULL, WNOHANG)) > 0)
\t\tdprintf("Reaped %d\\n", pid);
#endif'''
include='#ifdef USE_WR_BAND_STEERING_PROFILE\n#include "wr-band-child-owner.h"\n#endif\n'
copies={name:(Path(__file__).parent/name).read_bytes() for name in ['child-owner.c','child-owner.h']}
init.write_text(include+text.replace(old,new))
make.write_text(mk.replace('OBJS += wr-band-profile-policy.o\n','OBJS += wr-band-profile-policy.o wr-band-child-owner.o\n'))
for name,data in copies.items():
    (rc/('wr-band-'+name)).write_bytes(data.replace(b'"child-owner.h"',b'"wr-band-child-owner.h"'))
print('Registered gated owned-child reaper; spawn/lifecycle binding still pending')
