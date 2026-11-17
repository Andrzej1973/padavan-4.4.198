from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
here=Path(__file__).resolve().parent
original=Path(sys.argv[1]).read_text()
commit=runpy.run_path(str(here/'prepare-nvram-commit-order.py'))['transform']
batch=runpy.run_path(str(here/'prepare-nvram-batch-candidate.py'))['transform']
native_order=runpy.run_path(str(here.parent/'band-steering/prepare-nvram-commit-order.py'))['prepare']
native_flash=runpy.run_path(str(here.parent/'band-steering/prepare-nvram-flash-readback.py'))['prepare']
ordered=native_order(original)
with_flash=native_flash(ordered)
modern=commit(original)
def body(text):
 start=text.index('nvram_commit(void)\n{')
 return text[start:text.index('\n}',start)+2]
assert commit(ordered)==ordered and commit(with_flash)==with_flash
for source in (modern,ordered.replace('/* Regenerate NVRAM */','/* changed generation boundary */',1)):
 try:commit(source)
 except ValueError:pass
 else:raise AssertionError('Unreviewed or repeated Modern transform must refuse')
generated=batch(with_flash)
assert body(generated)==body(ordered)
for marker in ('case WR_NVRAM_IOCTL_READ_FLASH:', 'case WR_NVRAM_IOCTL_SAVE_PROFILE:', 'case WR_NVRAM_IOCTL_BATCH_V1:'):
 assert generated.count(marker)==1
try:batch(generated)
except ValueError:pass
else:raise AssertionError('Repeated batch candidate must refuse')
fixture=(here/'nvram-commit-order-fixture.c.inc').read_text()
with tempfile.TemporaryDirectory(prefix='wr-nvram-composition-') as directory:
 root=Path(directory)
 for index,source in enumerate((original,modern,ordered,with_flash,generated)):
  cfile=root/('case'+str(index)+'.c');binary=root/('case'+str(index))
  cfile.write_text('#define FIXED '+str(int(index!=0))+'\n'+fixture.replace('/* ACTUAL_COMMIT */','static int\n'+body(source)))
  subprocess.run(['gcc','-std=gnu11','-pthread','-Wall','-Wextra','-Werror',
   '-fsanitize=address,undefined','-fno-pie','-no-pie',str(cfile),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=15)
 wire=root/'wire.c';binary=root/'wire'
 wire.write_text('#include "nvram-batch-wire.h"\n#include "native-flash-wire.h"\n'
  '_Static_assert(WR_NVRAM_IOCTL_BATCH_V1!=WR_NVRAM_IOCTL_READ_FLASH,"read collision");\n'
  '_Static_assert(WR_NVRAM_IOCTL_BATCH_V1!=WR_NVRAM_IOCTL_SAVE_PROFILE,"save collision");\nint main(void){return 0;}\n')
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(here),'-I'+str(here.parent/'iot'),str(wire),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=5)
print('PASS original race counterexample and both reviewed mutex repairs; exact IoT/readback/batch composition retains serialized commit, native dispatch and distinct ioctl encodings; host only')
