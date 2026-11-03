#!/usr/bin/env python3
"""Pin optional verification to an ancestor commit without moving the branch."""
import argparse,json,os,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--revision',default='')
p.add_argument('--dispatch-sha',required=True)
p.add_argument('--allow-override',choices=('true','false'),default='false')
a=p.parse_args()
def git(*args):
 return subprocess.check_output(['git',*args],text=True).strip()
if not re.fullmatch('[0-9a-f]{40}',a.dispatch_sha):p.error('full dispatch SHA required')
if git('rev-parse','HEAD')!=a.dispatch_sha:p.error('checkout differs from dispatch SHA')
if a.revision:
 if a.allow_override!='true':p.error('revision override is optional-dispatch only')
 if not re.fullmatch('[0-9a-f]{40}',a.revision):p.error('full lowercase revision SHA required')
 if subprocess.run(['git','merge-base','--is-ancestor',a.revision,a.dispatch_sha]).returncode:
  p.error('requested revision is not an ancestor of dispatch commit')
 if git('status','--porcelain'):p.error('revision checkout requires a clean CI tree')
 subprocess.run(['git','checkout','--detach',a.revision],check=True)
sha=git('rev-parse','HEAD')
report={'dispatch_revision':a.dispatch_sha,'requested_revision':a.revision,
        'verified_revision':sha,'runtime_verified':False}
Path('verification-source.json').write_text(json.dumps(report,indent=2)+'\n')
if os.environ.get('GITHUB_OUTPUT'):
 with open(os.environ['GITHUB_OUTPUT'],'a') as out:out.write('sha='+sha+'\n')
print(json.dumps(report))
