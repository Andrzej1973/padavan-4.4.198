"""Actual staging with synthetic target-pair and ROMFS fixtures."""
from pathlib import Path
here=Path(__file__).resolve().parent
source=(here/'check-package-candidate-pair.py').read_text()
anchor=" mutations=["
position=source.index(anchor)
source=source[:position]+r'''
 import os
 stage=runpy.run_path(str(here/'stage-candidate-romfs.py'))['stage']
 snapshot=runpy.run_path(str(here/'stage-candidate-romfs.py'))['snapshot']
 # Keep every fixture within the owning TemporaryDirectory.
 baseline=root/'baseline';baseline.mkdir()
 paths={'sbin/rc':b'old rc','usr/sbin/httpd':b'old httpd','usr/bin/iappd.sh':b'old script',
        'lib/modules/4.4.198/kernel/drivers/net/wireless/mt76x3_ap.ko':b'old module',
        'etc/defaults':b'saved defaults preserved','www/index.asp':b'classic preserved'}
 for n,b in paths.items():
  p=baseline/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);p.chmod(0o755 if n.startswith(('sbin/','usr/')) else 0o644)
 (baseline/'init').symlink_to('sbin/rc');(baseline/'sbin/init').symlink_to('rc')
 before=snapshot(baseline)
 kernel=root/'baseline-kernel.config';kernel.write_text('# CONFIG_PM is not set\n')
 # Results and output must be disjoint. Fixture results live at root, so stage
 # only the required files into their own subtree like actual CI artifacts.
 results=root/'results';results.mkdir()
 for p in list(root.rglob('*')):
  if p.is_file() and not p.is_symlink() and not p.is_relative_to(baseline) and not p.is_relative_to(results) and p!=kernel:
   target=results/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
 pair=build(results,'a'*40)
 report=stage(baseline,results,pair,'a'*40,kernel,root/'output')
 assert report['isolated_romfs_staged'] and report['baseline_unchanged'] and not report['trx_built']
 assert snapshot(baseline)==before and os.readlink(root/'output/init')=='sbin/rc'
 assert (root/'output/sbin/rc').read_bytes()==rc
 assert (root/'output/etc/defaults').read_bytes()==b'saved defaults preserved'
 for fault in range(4):
  output=root/('refused-'+str(fault));restore=None
  if fault==0:kernel.write_text('CONFIG_PM=y\n')
  if fault==1:
   restore=baseline/'lib/modules/4.4.198/duplicate/mt76x3_ap.ko';restore.parent.mkdir();restore.write_bytes(b'duplicate')
  if fault==2:
   restore=baseline/'sbin/rc';restore.unlink();restore.symlink_to('../etc/defaults')
  wrong=dict(pair)
  if fault==3:wrong['source_revision']='b'*40
  try:stage(baseline,results,wrong,'a'*40,kernel,output)
  except ValueError:pass
  else:raise AssertionError('Unsafe ROMFS accepted '+str(fault))
  assert not output.exists()
  kernel.write_text('# CONFIG_PM is not set\n')
  if restore:
   restore.unlink()
   if fault==1:restore.parent.rmdir()
   else:restore.write_bytes(paths['sbin/rc']);restore.chmod(0o755)
 for name in ('modern','hybrid'):
  retired=baseline/'www'/name
  retired.symlink_to('index.asp')
  output=root/('refused-'+name)
  try:
   stage(baseline,results,pair,'a'*40,kernel,output)
  except ValueError as error:
   assert 'retired WebUI in baseline: www/'+name in str(error)
  else:
   raise AssertionError('Retired WebUI accepted: '+name)
  assert not output.exists() and retired.is_symlink()
  retired.unlink()
 assert snapshot(baseline)==before
print('PASS isolated ROMFS staging: exact pair, discovered unique module path, modes/multicall links/unrelated settings preserved; kernel mismatch, duplicate module, alias and wrong source refuse before output; synthetic target inputs only')
'''
exec(compile(source,str(here/'check-package-candidate-pair.py'),'exec'),{'__file__':str(here/'check-package-candidate-pair.py')})
