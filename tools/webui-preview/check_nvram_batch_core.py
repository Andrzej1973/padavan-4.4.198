#!/usr/bin/env python3
"""Actual pinned NVRAM hash/allocator plus isolated batch prototype; host only."""
import hashlib,importlib.util,json,pathlib,subprocess,sys,tarfile,tempfile
from nvram_abi_probe import client_source,read_record
here=pathlib.Path(__file__).resolve().parent
with tarfile.open(sys.argv[1]) as archive:
    common=archive.extractfile('trunk/linux-4.4.x/drivers/nvram/nvram.c').read().decode()
    linux=archive.extractfile('trunk/linux-4.4.x/drivers/nvram/nvram_linux.c').read().decode()
    header=archive.extractfile('trunk/linux-4.4.x/include/nvram/bcmnvram.h').read().decode()
    cgi=archive.extractfile('trunk/user/httpd/cgi.c').read().decode()
# Match the isolated Modern body preparer's sole CGI correction exactly.
assert cgi.count('strncpy(s, s + 2, strlen(s) + 1);')==1
cgi=cgi.replace('strncpy(s, s + 2, strlen(s) + 1);','memmove(s, s + 2, strlen(s + 2) + 1);')
spec=importlib.util.spec_from_file_location('nvram_batch',here/'prepare-nvram-batch-candidate.py')
generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
generated=generator.transform(linux)
expected_core=(here/'nvram-batch-core.c.inc').read_text().replace('static int wr_nvram_batch_candidate(', 'int wr_nvram_batch_candidate(',1)
assert expected_core in generated
assert (here/'nvram-batch-user.c.inc').read_text() in generated
assert generated.index('_nvram_free(struct')<generated.index('int wr_nvram_batch_candidate(')<generated.index('nvram_commit(void)')
for invalid in (generated,linux.replace('_nvram_free(struct nvram_tuple *t)','_nvram_free(struct nvram_tuple *renamed)')):
    try:generator.transform(invalid)
    except ValueError:pass
    else:raise AssertionError('Changed/repeated generation must refuse')
print('PASS exact batch core target composition and changed/repeated source rejection; candidate SHA256',hashlib.sha256(generated.encode()).hexdigest())
def fn(text,marker,prefix=''):
    a=text.index(marker);return prefix+text[a:text.index('\n}',a)+2]+'\n'
prefix=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
typedef unsigned int uint;
#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))
#define ARRAYSIZE ARRAY_SIZE
#define NVRAM_MAX_PARAM_LEN 64
#define NVRAM_VALUES_SPACE 8192
#define GFP_ATOMIC 0
struct nvram_tuple {char *name,*value;uint32_t val_len:31,val_tmp:1;struct nvram_tuple *next;};
static struct nvram_tuple *nvram_hash[257];
static char arena[NVRAM_VALUES_SPACE],*nvram_values=arena;
static unsigned long nvram_offset;
static int nvram_lock,depth,allocations,live,fail_at;
static void *user_owned;
static int user_frees;
static pthread_mutex_t host_mutex=PTHREAD_MUTEX_INITIALIZER;
#define spin_lock_irqsave(lock,flags) do{(void)(lock);assert(!pthread_mutex_lock(&host_mutex));assert(!depth);depth=1;(flags)=0;}while(0)
#define spin_unlock_irqrestore(lock,flags) do{(void)(lock);(void)(flags);assert(depth==1);depth=0;assert(!pthread_mutex_unlock(&host_mutex));}while(0)
static void *kmalloc(size_t bytes,int mode){(void)mode;assert(depth==1);allocations++;if(fail_at&&allocations==fail_at)return NULL;void *p=malloc(bytes);if(p)live++;return p;}
static void kfree(void *p){if(p){if(p==user_owned){for(unsigned int i=0;i<5264;i++)assert(!((unsigned char *)p)[i]);user_owned=NULL;user_frees++;free(p);}else{assert(depth==1);live--;free(p);}}}
'''
actual=fn(common,'hash(const char *s)','static inline uint\n')+fn(linux,'_nvram_realloc(struct','struct nvram_tuple *\n')+fn(linux,'_nvram_free(struct','void\n')+fn(common,'_nvram_get(const char *name)\n{','char *\n')+fn(common,'_nvram_set(const char *name, const char *value, int is_temp)\n{','int\n')
ioctl_constants='\n'.join(line for line in header.splitlines() if line.startswith('#define NVRAM_IOCTL_'))+'\n'
ioctl_stubs=r'''
struct file {int unused;};
typedef int anvram_ioctl_t;
static int legacy_calls;
static int nvram_commit(void){legacy_calls++;return 71;}
static int nvram_clear(void){legacy_calls++;return 72;}
static int user_nvram_set(anvram_ioctl_t *p){(void)p;legacy_calls++;return 73;}
static int user_nvram_get(anvram_ioctl_t *p){(void)p;legacy_calls++;return 74;}
'''
ioctl_body=fn(generated,'dev_nvram_ioctl(struct file *file, unsigned int req, unsigned long arg)\n{','static long\n').replace('struct file *file,','struct file *file __attribute__((unused)),',1)
fixture=(here/'nvram-batch-fixture.c.inc').read_text()
reply=(here/'guest-json-output.c.inc').read_text().split('static void do_wr_modern_guest_apply(')[0]
handler=reply+(here/'guest-batch-http.c.inc').read_text()
handler=handler.replace('fopen("/dev/null","w")','fixture_batch_sink("/dev/null","w")').replace('open("/dev/nvram",','fixture_nvram_open("/dev/nvram",').replace('close(fd);','fixture_nvram_close(fd);')
http_fixture=(here/'guest-batch-http-fixture.c.inc').read_text().replace('/* HTTP_HANDLER */',handler)
assert http_fixture.count('return guest_cgi(ctx,key);')==1
http_fixture=http_fixture.replace('return guest_cgi(ctx,key);','return http_actual_cgi?get_cgi((char *)key):guest_cgi(ctx,key);')
http_fixture='static int http_actual_cgi;\n'+http_fixture
http_fixture+='\n'+(here/'guest-batch-cgi-fixture.c.inc').read_text()
fixture=fixture.replace('int main(void)',(here/'guest-batch-fixture.c.inc').read_text()+'\n'+http_fixture+'\nint main(void)',1)
fixture=fixture.replace('guest_batch_http_cases();','guest_batch_http_cases();guest_batch_cgi_cases();',1)
user_fixture=(here/'nvram-batch-user-fixture.c.inc').read_text().replace('/* USER_ENTRY */',(here/'nvram-batch-user.c.inc').read_text())
with tempfile.TemporaryDirectory(prefix='wr-nvram-batch-core-') as scratch:
    root=pathlib.Path(scratch);(root/'fixture.c').write_text(prefix+cgi+actual+(here/'nvram-batch-core.c.inc').read_text()+(here/'nvram-batch-wire.h').read_text()+(here/'nvram-batch-wire.c.inc').read_text()+user_fixture+ioctl_constants+ioctl_stubs+ioctl_body+fixture)
    subprocess.run(['gcc','-std=gnu99','-Wall','-Wextra','-Werror','-pthread','-fsanitize=address,undefined','-fno-pie','-no-pie','-I',str(here),'-I',str(here.parent/'shared-wifi'),str(root/'fixture.c'),'-o',str(root/'fixture')],check=True)
    executed=subprocess.run([str(root/'fixture')],capture_output=True,text=True)
    if executed.returncode:
        print(executed.stdout);print(executed.stderr);executed.check_returncode()
    replies=[]
    for line in executed.stdout.splitlines():
        if line.startswith('BATCH_HTTP_REPLY '):replies.append(json.loads(line[len('BATCH_HTTP_REPLY '):]))
        else:print(line)
    assert len(replies)==23
    subprocess.run(['node',str(here/'check_guest_client.js'),'--batch-http-replies'],input=json.dumps(replies),text=True,check=True)
    (root/'client.c').write_text(client_source())
    subprocess.run(['gcc','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-I',str(here),'-I',str(here.parent/'shared-wifi'),'-c',str(root/'client.c'),'-o',str(root/'client.o')],check=True)
    host_abi=read_record('objcopy',root/'fixture',root/'host-abi.bin')
    client_abi=read_record('objcopy',root/'client.o',root/'client-abi.bin')
    assert host_abi==client_abi
    print('PASS native host/client compiled ABI record match',json.dumps(host_abi),'MIPS acceptance still pending')
    size=sum(p.stat().st_size for p in root.iterdir());print('Owned scratch bytes removed',size)
assert not root.exists()
print('Pinned source hashes',json.dumps({'common':hashlib.sha256(common.encode()).hexdigest(),'allocator':hashlib.sha256(linux.encode()).hexdigest(),'header':hashlib.sha256(header.encode()).hexdigest()}))
