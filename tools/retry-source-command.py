#!/usr/bin/env python3
"""Retry a source-transfer command; keep argv intact and bound each attempt."""
import argparse
import subprocess
import time

def run(command, execute=subprocess.run, pause=time.sleep):
    for attempt in range(3):
        try:
            result=execute(command,timeout=300,check=False)
            status=result.returncode
        except subprocess.TimeoutExpired:
            status=124
        if status==0:return 0
        if attempt<2:
            print('Source command failed; retrying attempt '+str(attempt+2)+'/3',flush=True)
            pause(10*(attempt+1))
    return status if status>0 else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    if not args.command:parser.error('command required')
    raise SystemExit(run(args.command))
