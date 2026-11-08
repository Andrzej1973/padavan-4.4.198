"""Normalize only the explicit system ccache prefix; verify compiler separately."""
from pathlib import Path
import shutil

def unwrap_ccache(argv):
 argv=list(argv)
 if not argv:return argv
 if Path(argv[0]).name!='ccache':return argv
 if argv[0] not in ('ccache','/usr/bin/ccache'):
  raise RuntimeError('Untrusted ccache executable path')
 found=shutil.which(argv[0])
 if not found or Path(found).resolve()!=Path('/usr/bin/ccache').resolve():
  raise RuntimeError('Expected installed system ccache')
 if len(argv)<2 or argv[1].startswith('-'):
  raise RuntimeError('Expected compiler immediately after ccache')
 return argv[1:]
