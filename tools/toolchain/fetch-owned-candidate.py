#!/usr/bin/env python3
"""Fetch the exact candidate/report from owned Release with verified cache reuse."""
import importlib.util,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
owned=module('owned_inputs',HERE.parent/'prepare-owned-build-dependencies.py')
installer=module('candidate_installer',HERE/'install-candidate.py')

def fetch(destination,cache,manifest,download=owned.download):
 if manifest.get('schema')!=1 or manifest.get('generator_revision')!='5ef6a8577ae24be27d8d81b3fe44a587d8491a16' or manifest.get('source_run')!=42467546674:raise ValueError('Unreviewed owned candidate manifest')
 files=manifest['files']
 if len(files)!=2 or {v['filename'] for v in files}!={'result.json','mipsel-linux-uclibc-source-candidate.tar.xz'}:raise ValueError('Unexpected candidate file set')
 for item in files:
  if not re.fullmatch(r'https://api.github.com/repos/Andrzej1973/padavan-4\.4\.198/releases/assets/[0-9]+',item['url']) or not re.fullmatch('[0-9a-f]{64}',item['sha256']) or type(item['bytes']) is not int or item['bytes']<=0:raise ValueError('Invalid owned candidate pin')
 destination.mkdir(parents=True,exist_ok=True)
 # Reuse the existing tested partial-download/cache/hash machinery.
 entries=[dict(item,directory='.') for item in files]
 owned.seed(destination,cache,entries,download)
 for item in files:
  if (destination/item['filename']).stat().st_size!=item['bytes']:raise ValueError('Owned candidate size mismatch')
 report=json.loads((destination/'result.json').read_text())
 installer.validate(report,destination/'mipsel-linux-uclibc-source-candidate.tar.xz')
 print('PASS owned candidate/report SHA256, sizes and generator/ABI provenance; original control retained')

if __name__=='__main__':
 manifest=json.loads((ROOT/'configs/owned-source-toolchain.json').read_text())
 fetch(Path(sys.argv[1]),Path(sys.argv[2]),manifest)
