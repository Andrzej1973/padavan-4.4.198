#!/usr/bin/env python3
"""Install a verified source-build artifact into an empty candidate prefix."""
import hashlib,json,sys,tarfile
from pathlib import Path

def candidate_filter(member,destination):
 """Keep data-filter protections with correct symlink-relative resolution.

 Ubuntu 22.04's Python 3.10 data_filter resolves symlink targets relative to
 the extraction root (hardlink semantics). A nested ../../ link can therefore
 be rejected despite remaining inside the prefix. Validate its actual target
 ourselves, then let data_filter check the member path, type and metadata.
 Hardlinks still use the unmodified standard filter.
 """
 if not member.issym():return tarfile.data_filter(member,destination)
 if Path(member.linkname).is_absolute():raise tarfile.AbsoluteLinkError(member)
 root=Path(destination).resolve()
 if (root/member.name).resolve()==root:raise tarfile.OutsideDestinationError(member,str(root))
 # Symlinks are relative to their containing directory, never the tar root.
 target=(root/Path(member.name.rstrip('/')).parent/member.linkname).resolve()
 if not target.is_relative_to(root):raise tarfile.LinkOutsideDestinationError(member,str(target))
 # Only the already-checked link target is neutralized for the older filter;
 # traversal through member.name, ownership/modes and special files stay gated.
 checked=tarfile.data_filter(member.replace(linkname='.'),destination)
 return checked.replace(linkname=member.linkname)

def validate(report,archive):
 if report.get('project_revision')!='5ef6a8577ae24be27d8d81b3fe44a587d8491a16':raise ValueError('Unreviewed generator revision')
 for key in ['relocation_tested','qemu_user_verified']:
  if report.get(key) is not True:raise ValueError('Missing '+key)
 if report.get('production_promoted') is not False:raise ValueError('Unexpected promotion')
 if (report.get('gcc'),report.get('libc'),report.get('linux_headers'))!=('10.5.0','1.0.48','4.4.198'):raise ValueError('Wrong compiler ABI')
 expected=report['archives'][archive.name]
 if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected['sha256'] or archive.stat().st_size!=expected['bytes']:raise ValueError('Candidate archive hash mismatch')

def install(source,dest):
 archive=source/'mipsel-linux-uclibc-source-candidate.tar.xz';r=json.loads((source/'result.json').read_text());validate(r,archive)
 if dest.exists() and any(dest.iterdir()):raise ValueError('Destination must be empty')
 dest.mkdir(parents=True,exist_ok=True)
 with tarfile.open(archive) as t:
  # data filter checks traversal, special files and escaping symlinks.
  t.extractall(dest,filter=candidate_filter)
 if not (dest/'bin/mipsel-linux-uclibc-gcc').is_file():raise ValueError('Missing compiler')
 Path('toolchain-sha256.txt').write_text(r['archives'][archive.name]['sha256']+'  '+archive.name+'\n')
 print('PASS exact source-built candidate installed; no production promotion')
if __name__=='__main__':install(Path(sys.argv[1]),Path(sys.argv[2]))
