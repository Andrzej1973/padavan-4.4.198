#!/usr/bin/env python3
"""Preprocess with an actual Kbuild command; ceiling evidence, not live capacity."""
import argparse,json,re,shlex,subprocess,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('kernel',type=Path);p.add_argument('radio',choices=['mt76x2','mt76x3']);p.add_argument('--compiler',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=a.kernel.resolve();driver='drivers/net/wireless/mediatek/'+a.radio
cmdfile=root/(driver+'/chips/.rtmp_chip.o.cmd')
s=cmdfile.read_text(encoding='utf-8');commands=re.findall(r'^cmd_.*? := (.+)$',s,re.M)
if len(commands)!=1:raise SystemExit('Expected one actual Kbuild compiler command')
args=shlex.split(commands[0]);compiler=Path(args[0])
if not compiler.is_absolute():
 if '/' in args[0]:compiler=root/compiler
 else:
  resolved=shutil.which(args[0])
  if not resolved:raise SystemExit('Kbuild compiler is absent from the build PATH')
  compiler=Path(resolved)
if compiler.resolve()!=a.compiler.resolve():raise SystemExit('Kbuild compiler does not match requested pinned compiler')
if any(x in (';','&&','||','|','>','<') for x in args):raise SystemExit('Unexpected compound Kbuild command')
filtered=[];i=1
while i<len(args):
 x=args[i]
 if x in ('-o','-MF','-MT','-MQ'):i+=2;continue
 if x in ('-c','-MD','-MMD','-MP') or x.startswith('-Wp,-MD,') or x.startswith('-Wp,-MMD,'):i+=1;continue
 filtered.append(x);i+=1
result=subprocess.run([str(a.compiler.resolve())]+filtered+['-E','-dM'],cwd=root,text=True,capture_output=True)
if result.returncode:raise SystemExit('Target preprocessing failed: ' + result.stderr[-2000:])
macros={m.group(1):m.group(2).strip() for m in re.finditer(r'^#define ([A-Za-z_][A-Za-z0-9_]*) (.*)$',result.stdout,re.M)}
# A valueless feature define may appear without a trailing value.
mbss=bool(re.search(r'^#define MBSS_SUPPORT(?:\s|$)',result.stdout,re.M))
ceiling=macros.get('HW_BEACON_MAX_NUM','')
if not mbss or not re.fullmatch(r'[0-9]+',ceiling) or int(ceiling)<3:raise SystemExit('Compiled driver cannot establish a three-BSS array ceiling')
report={'radio':a.radio,'effective_mbss_support':mbss,'hardware_array_ceiling':int(ceiling),'max_mesh_num':macros.get('MAX_MESH_NUM'),'max_apcli_num':macros.get('MAX_APCLI_NUM'),'source_command':str(cmdfile.relative_to(root)),'runtime_verified':False,'scope':'Effective Kbuild preprocessing and array ceiling; chip capability initialization and live third BSS require separate evidence'}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASS effective '+a.radio+' MBSS support and three-BSS array ceiling; runtime unverified')
