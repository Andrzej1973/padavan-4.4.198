"""Actual selected lifetime observer plus physical INITIAL claim/cleanup."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-initial-saved-physical.py').read_text()
ns={'__file__':str(here/'check-initial-saved-physical.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<saved physical fixture>','exec'),ns)
code=ns['code']
old='int wr_iot_initial_restart_selected_current(const unsigned char*n,const struct wr_iot_idle_result*r){(void)n;(void)r;assert(0);return 0;}'
assert code.count(old)==1
code=code.replace(old,'').replace('int wr_iot_rc_boot_idle(void){return 0;}','int wr_iot_rc_boot_idle(void){return 1;}')
hooks=r'''
#include <fcntl.h>
static int drift,probe_reads;
int wr_iot_service_guard_dup(void){assert(depth==1);return open("/dev/null",O_RDONLY);}
int wr_iot_rc_mode_read(struct wr_iot_rc_mode *m){assert(depth==1);*m=(struct wr_iot_rc_mode){1,1,0};return 1;}
int wr_iot_request_initial_off_current(void){assert(depth==1);return 1;}
unsigned if_nametoindex(const char*n){assert(depth==1&&!strcmp(n,"br-iot"));return 0;}
int wr_iot_bss_is_down(void){assert(depth==1);return 1;}
int wr_iot_dns_activation_recovery_state(void){assert(depth==1);return 0;}
int wr_iot_driver_initial_idle_read(const unsigned char*n,struct wr_iot_idle_result*r){
 assert(depth==1&&wr_iot_rc_shutdown.active&&n[0]==7&&!downs&&!initial_calls);
 probe_reads++;*r=(struct wr_iot_idle_result){11,12,9+(unsigned long long)probe_reads};
 if(drift==1)r->epoch++;
 if(drift==2)r->generation++;
 if(drift==3)r->serial=9;
 if(drift==4&&probe_reads==2)wr_iot_rc_shutdown.pending=SIGTERM;
 return drift!=5;
}
void wr_iot_rc_initial_restart_detach_commit(void){assert(0);}
'''
code=code.replace('int main(int argc,char **argv){',hooks+'\nint main(int argc,char **argv){',1)
code=code.replace('saved_ok=argc!=2;saved_enabled=argc!=3;', 'saved_ok=1;saved_enabled=1;drift=argc==2?atoi(argv[1]):0;unsigned char nonce[16]={7};struct wr_iot_idle_result selected={11,12,9};')
code=code.replace('wr_iot_rc_physical_begin_initial_saved(&intent)', 'wr_iot_rc_physical_begin_initial_selected(&intent,nonce,&selected)')
code=code.replace('(void)handler;(void)argv;', '(void)argv;struct sigaction action={0};action.sa_handler=handler;sigemptyset(&action.sa_mask);assert(!sigaction(SIGTERM,&action,NULL));')
code=code.replace('if(!saved_ok){','if(drift){').replace('assert(physical.finishing==-1&&!physical.initial_saved);','assert(physical.finishing==-1&&physical.initial_saved);')
with tempfile.TemporaryDirectory(prefix='wr-initial-selected-compose-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),str(here/'initial-restart-select.c'),'-o',str(b)],check=True)
 for args in [[],['1'],['2'],['3'],['4'],['5']]:subprocess.run([str(b)]+args,check=True,timeout=15)
print('PASS actual selected-current observer plus physical INITIAL claim: current lifetime proceeds, epoch/generation/serial/TERM/read failure retain claim then clean without ARM/DOWN; driver/software adapters injected')
