#!/usr/bin/env python3
"""Retry a source-transfer command; keep argv intact and bound each attempt."""
import argparse
import os
from pathlib import Path
import signal
import stat
import subprocess
import time

def execute_source(command,timeout,check=False):
    # These workflow-owned source repos are exclusive to this CI step.
    # Never remove an existing lock or touch the shared project checkout.
    lock=None
    if (len(command)>3 and command[:2]==['git','-C'] and command[3]=='fetch'
            and command[2] in ('padavan-4.4','amnezia-source')):
        gitdir=Path(command[2])/'.git'
        candidate=gitdir/'shallow.lock'
        if (not Path(command[2]).is_symlink() and gitdir.is_dir() and
                not gitdir.is_symlink() and not candidate.exists() and not candidate.is_symlink()):
            lock=candidate
    process=subprocess.Popen(command,start_new_session=True)
    try:
        status=process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        # subprocess.run kills only the parent. Git transport/index-pack must
        # also stop before retrying or considering this attempt's lock stale.
        try:os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:pass
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.wait()
        if lock is not None:
            try:
                if stat.S_ISREG(lock.lstat().st_mode):
                    lock.unlink()
                    print('Removed timed-out source fetch shallow lock: '+str(lock),flush=True)
            except FileNotFoundError:pass
        raise
    return subprocess.CompletedProcess(command,status)

def run(command, execute=execute_source, pause=time.sleep, timeout=300):
    for attempt in range(3):
        try:
            result=execute(command,timeout=timeout,check=False)
            status=result.returncode
        except subprocess.TimeoutExpired:
            print('Source command timed out after '+str(timeout)+' seconds; process group stopped',flush=True)
            status=124
        if status==0:return 0
        if attempt<2:
            print('Source command failed; retrying attempt '+str(attempt+2)+'/3',flush=True)
            pause(10*(attempt+1))
    return status if status>0 else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout',type=int,default=300)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    if not args.command:parser.error('command required')
    if not 0<args.timeout<=1800:parser.error('timeout must be 1..1800 seconds')
    raise SystemExit(run(args.command,timeout=args.timeout))
