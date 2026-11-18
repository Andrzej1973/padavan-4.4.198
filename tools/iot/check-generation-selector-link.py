"""Real native weak/strong link, target-specific flags and negative evidence cases."""
from pathlib import Path
import ast
import runpy
import subprocess
import tempfile
here=Path(__file__).resolve().parent
verify=runpy.run_path(str(here/'verify-generation-selector-link.py'))['verify']
binding=runpy.run_path(str(here/'generation-selector-source.py'))
prepare_map=runpy.run_path(str(here/'prepare-runtime-link-map.py'))['prepare']
producer=ast.parse((here/'prepare-rc.py').read_text())
include=next(ast.literal_eval(n.value) for n in producer.body if isinstance(n,ast.Assign)
             and any(isinstance(t,ast.Name) and t.id=='include' for t in n.targets))
prepared=binding['bind'](include)
assert binding['WEAK'] not in prepared and prepared.count('#include "wr-iot/generation-profile.h"')==1
for wrong in [prepared,include+binding['WEAK'],include.replace('return 0;','return 1;')]:
 try:binding['bind'](wrong)
 except ValueError:pass
 else:raise AssertionError('Unrecognized/repeated selector binding accepted')
with tempfile.TemporaryDirectory(prefix='wr-selector-link-') as directory:
 root=Path(directory);symbol='wr_iot_generation_profile_request'
 (root/'ralink.c').write_text('__attribute__((weak)) int '+symbol+'(void){return 1;}\nint main(void){return '+symbol+'()==7?0:2;}\n')
 (root/'store.c').write_text('int '+symbol+'(void){return 7;}\n')
 for source,obj in [('ralink.c','ralink.o'),('store.c','wr-iot-saved-config-store.o')]:
  subprocess.run(['gcc','-O2','-c',str(root/source),'-o',str(root/obj)],check=True)
 # Match the SDK: `all` links EXEC=rc directly; there is no rc target recipe.
 native=('EXEC = rc\nLDFLAGS = -Wl,--as-needed\nOBJS = ralink.o wr-iot-saved-config-store.o\n'
         'all: $(OBJS) Makefile\n\t$(CC) -o $(EXEC) $(OBJS) $(LDFLAGS)\n\t$(STRIP) $(EXEC)\n')
 makefile=root/'Makefile';output=root/'rc-link-map.txt'
 # Reproduce optional1387: a target-specific rc flag never reaches all's link.
 makefile.write_text(native+'\nrc: override LDFLAGS += -Wl,-Map,'+str(output)+',--cref\n')
 subprocess.run(['make','-C',str(root),'CC=gcc','STRIP=strip','all'],check=True,stdout=subprocess.DEVNULL)
 assert not output.exists()
 makefile.write_text(native);prepare_map(makefile,output)
 prepared=makefile.read_bytes()
 try:prepare_map(makefile,output)
 except ValueError:pass
 else:raise AssertionError('Repeated map preparation accepted')
 assert makefile.read_bytes()==prepared
 linked=subprocess.check_output(['make','-C',str(root),'CC=gcc','STRIP=strip','all'],text=True)
 assert '-Wl,--as-needed' in linked and '-Wl,-Map,' in linked and output.is_file()
 subprocess.run([str(root/'rc')],check=True)
 for name,command in [('generation-selector-store-symbols.txt',['nm',str(root/'wr-iot-saved-config-store.o')]),
                      ('generation-selector-caller-relocations.txt',['objdump','-dr',str(root/'ralink.o')])]:
  (root/name).write_bytes(subprocess.check_output(command))
 result=verify(root,root/'rc');assert result['selector_link_provider_verified'] and not result['runtime_verified']
 for name in result['input_sha256']:
  path=root/name;original=path.read_bytes();path.write_bytes(b'')
  try:verify(root,root/'rc')
  except ValueError:pass
  else:raise AssertionError('Missing evidence accepted: '+name)
  path.write_bytes(original)
 path=root/'rc-link-map.txt';original=path.read_text()
 path.write_text(original.replace('wr-iot-saved-config-store.o','wrong-provider.o'))
 try:verify(root,root/'rc')
 except ValueError:pass
 else:raise AssertionError('Wrong provider accepted')
print('PASS native RC all-target recipe reproduces old missing map; corrected scoped flags preserve linker options, execute strong override and verify stripped ELF/GNU map/relocations; target MIPS separately required')
