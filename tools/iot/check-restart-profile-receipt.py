"""Actual owned restore/profile finish and retained metadata receipt; temp IO."""
from pathlib import Path
import argparse,subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <unistd.h>
#include "restart-profile-receipt.h"
static int guard=1;
int wr_iot_service_guard_dup(void){return guard?dup(STDERR_FILENO):-1;}
int main(int argc,char**argv){
 assert(argc==2);struct wr_iot_radio_profile_state p={0};struct wr_iot_restart_profile_receipt r={0};
 FILE*f=fopen(argv[1],"w");assert(f&&fputs("baseline-secret\n",f)>=0&&!fclose(f));
 const char *paths[]={argv[1]};assert(wr_iot_bundle_capture(&p.files,paths,1));p.active=1;p.owner=getpid();
 assert(!wr_iot_restart_profile_receipt_take(&r,&p)&&!r.valid);
 struct wr_iot_restart_profile_receipt read_only={0};
 assert(wr_iot_restart_profile_receipt_cancel_take(&read_only,&p));
 assert(wr_iot_restart_profile_receipt_current(&read_only));
 p.files.pending=1;struct wr_iot_restart_profile_receipt refused={0};
 assert(!wr_iot_restart_profile_receipt_cancel_take(&refused,&p)&&!refused.valid);p.files.pending=0;
 assert(wr_iot_radio_profile_restore(&p));
 guard=0;assert(!wr_iot_restart_profile_receipt_take(&r,&p)&&!r.valid);guard=1;
 assert(wr_iot_restart_profile_receipt_take(&r,&p));assert(!wr_iot_restart_profile_receipt_take(&r,&p));
 assert(wr_iot_radio_profile_finish(&p)&&!p.active&&!p.files.saved[0].data);
 assert(wr_iot_restart_profile_receipt_current(&r));
 struct wr_iot_restart_profile_receipt malformed=r;
 malformed.owner=getpid()+1;assert(!wr_iot_restart_profile_receipt_current(&malformed));
 malformed=r;memset(malformed.path,'x',sizeof(malformed.path));assert(!wr_iot_restart_profile_receipt_current(&malformed));
 malformed=r;malformed.valid=0;assert(!wr_iot_restart_profile_receipt_current(&malformed));
 guard=0;assert(!wr_iot_restart_profile_receipt_current(&r));guard=1;
 struct wr_iot_restart_profile_receipt altered=r;
#if defined(__USE_MISC) || (!defined(__UCLIBC__) && defined(__USE_XOPEN2K8))
 altered.file.metadata.st_mtim.tv_nsec=(wr_iot_profile_mtime_nsec(&altered.file.metadata)+1)%1000000000;
#else
 altered.file.metadata.st_mtimensec=(wr_iot_profile_mtime_nsec(&altered.file.metadata)+1)%1000000000;
#endif
 assert(!wr_iot_restart_profile_receipt_current(&altered));
 altered=r;
#if defined(__USE_MISC) || (!defined(__UCLIBC__) && defined(__USE_XOPEN2K8))
 altered.file.metadata.st_ctim.tv_nsec=(wr_iot_profile_ctime_nsec(&altered.file.metadata)+1)%1000000000;
#else
 altered.file.metadata.st_ctimensec=(wr_iot_profile_ctime_nsec(&altered.file.metadata)+1)%1000000000;
#endif
 assert(!wr_iot_restart_profile_receipt_current(&altered));
 char foreign[1024];snprintf(foreign,sizeof(foreign),"%s.foreign",argv[1]);
 f=fopen(foreign,"w");assert(f&&fputs("baseline-secret\n",f)>=0&&!fclose(f)&&!rename(foreign,argv[1]));
 assert(!wr_iot_restart_profile_receipt_current(&r));assert(!unlink(argv[1]));
 assert(!wr_iot_restart_profile_receipt_current(&r));
 assert(!symlink("/dev/null",argv[1]));assert(!wr_iot_restart_profile_receipt_current(&r));assert(!unlink(argv[1]));
 puts("PASS restored-profile receipt: owned recovery required, no output on refusal, survives profile memory release, missing guard/foreign identical-content inode rejected; real file IO, guard actor injected; metadata identity only");
}
'''
parser=argparse.ArgumentParser()
parser.add_argument('--target-compiler',type=Path)
parser.add_argument('--target-sysroot',type=Path)
parser.add_argument('--qemu',type=Path)
args=parser.parse_args()
if any((args.target_compiler,args.target_sysroot,args.qemu)) and not all((args.target_compiler,args.target_sysroot,args.qemu)):
 parser.error('target compiler, sysroot and QEMU must be supplied together')
with tempfile.TemporaryDirectory(prefix='wr-profile-receipt-') as d:
 p=Path(d)/'test.c';b=Path(d)/'test'
 flags=['-mips32r2','-march=mips32r2','-mtune=1004kc'] if args.target_compiler else ['-fsanitize=address,undefined']
 for feature in ('_GNU_SOURCE','_POSIX_C_SOURCE 200809L\n#define _XOPEN_SOURCE 700'):
  p.write_text(code.replace('#define _GNU_SOURCE','#define '+feature))
  subprocess.run([str(args.target_compiler) if args.target_compiler else 'gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',*flags,'-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
  run=[str(args.qemu),'-L',str(args.target_sysroot)] if args.target_compiler else []
  subprocess.run(run+[str(b),str(Path(d)/'profile')],check=True,timeout=15)
