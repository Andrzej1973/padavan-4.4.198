#!/usr/bin/env python3
"""Seed exact verified archives before legacy make downloads; no source patching."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path

def valid(path,digest):
 if not path.is_file() or path.is_symlink():return False
 return hashlib.sha256(path.read_bytes()).hexdigest()==digest

def seed(root,cache,entries,fetch):
 cache.mkdir(parents=True,exist_ok=True)
 for entry in entries:
  directory=root/entry['directory'];name=entry['filename'];digest=entry['sha256']
  if not directory.is_dir():raise ValueError('Required dependency directory absent: '+str(directory))
  archive=cache/(digest+'-'+name);partial=archive.with_name(archive.name+'.part')
  try:
   if not valid(archive,digest):
    fetch(entry['url'],partial)
    if not valid(partial,digest):raise ValueError('Dependency SHA256 mismatch: '+name)
    partial.replace(archive)
   target=directory/name
   if target.is_symlink():raise ValueError('Refuse archive symlink: '+str(target))
   shutil.copyfile(archive,target)
   if not valid(target,digest):raise ValueError('Installed archive SHA mismatch')
  finally:
   if partial.exists():partial.unlink()
  print('Verified owned source:',name,digest)

def download(url,path):
 subprocess.run(['curl','--silent','--show-error','--fail','--location','--retry','3','--retry-all-errors','--connect-timeout','20','--max-time','180','-H','Accept: application/octet-stream','--output',str(path),url],check=True)
if __name__=='__main__':
 entries=json.loads(Path(__file__).resolve().parent.parent.joinpath('configs/owned-build-dependencies.json').read_text())
 seed(Path(sys.argv[1]),Path(sys.argv[2]),entries,download)
