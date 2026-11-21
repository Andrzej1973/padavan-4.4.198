#include <assert.h>
#include <errno.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NVRAM_SPACE 16
#define GFP_KERNEL 0
#define MTD_NVRAM_NAME "fixture"
#define NVRAM_MTD_OFFSET 0
#define printk(...) ((void)0)
struct nvram_header {unsigned char bytes[NVRAM_SPACE];};
static pthread_mutex_t nvram_lock=PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t nvram_sem=PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t control=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t changed=PTHREAD_COND_INITIALIZER;
static _Thread_local int identity;
static int nvram_major=1,ram,flash,snapshot_a,release_a,b_attempt,snapshot_b;
static int generate_error,write_error,alloc_fail,writes;
static _Atomic int alloc_count,live;
static int schedule;
static void *kzalloc(size_t n,int mode){(void)mode;alloc_count++;if(alloc_count==alloc_fail)return NULL;void *p=calloc(1,n);if(p)live++;return p;}
static void kfree(void *p){if(p){live--;free(p);}}
static void host_spin_unlock(void)
{
 assert(!pthread_mutex_unlock(&nvram_lock));
 if(schedule&&identity==1){
  assert(!pthread_mutex_lock(&control));snapshot_a=1;assert(!pthread_cond_broadcast(&changed));
  while(!release_a)assert(!pthread_cond_wait(&changed,&control));
  assert(!pthread_mutex_unlock(&control));
 }
}
#define spin_lock_irqsave(lock,flags) do{(flags)=0;assert(!pthread_mutex_lock(lock));}while(0)
#define spin_unlock_irqrestore(lock,flags) do{(void)(lock);(void)(flags);host_spin_unlock();}while(0)
static void mutex_lock(pthread_mutex_t *lock)
{
 if(schedule&&identity==2){
  assert(!pthread_mutex_lock(&control));b_attempt=1;assert(!pthread_cond_broadcast(&changed));assert(!pthread_mutex_unlock(&control));
 }
 assert(!pthread_mutex_lock(lock));
}
static void mutex_unlock(pthread_mutex_t *lock){assert(!pthread_mutex_unlock(lock));}
static int _nvram_generate(struct nvram_header *header,int temporary)
{
 (void)temporary;memset(header,ram,NVRAM_SPACE);
 if(schedule&&identity==2){assert(!pthread_mutex_lock(&control));snapshot_b=1;assert(!pthread_mutex_unlock(&control));}
 return generate_error;
}
static int ra_mtd_read_nm(const char *name,int offset,size_t bytes,void *out)
{(void)name;(void)offset;memset(out,flash,bytes);return 0;}
static int ra_mtd_write_nm(const char *name,int offset,size_t bytes,const void *in)
{(void)name;(void)offset;(void)bytes;writes++;if(write_error)return write_error;flash=*(const unsigned char *)in;return 0;}
/* ACTUAL_COMMIT */
static void *run_commit(void *id){identity=(int)(long)id;assert(!nvram_commit());return NULL;}
static void assert_unlocked(void){assert(!pthread_mutex_trylock(&nvram_sem));assert(!pthread_mutex_unlock(&nvram_sem));assert(!live);}
int main(void)
{
 pthread_t a,b;schedule=1;ram=1;
 assert(!pthread_create(&a,NULL,run_commit,(void *)1L));
 assert(!pthread_mutex_lock(&control));while(!snapshot_a)assert(!pthread_cond_wait(&changed,&control));assert(!pthread_mutex_unlock(&control));
 assert(!pthread_mutex_lock(&nvram_lock));ram=2;assert(!pthread_mutex_unlock(&nvram_lock));
 assert(!pthread_create(&b,NULL,run_commit,(void *)2L));
 assert(!pthread_mutex_lock(&control));while(!b_attempt)assert(!pthread_cond_wait(&changed,&control));
 assert(snapshot_b==!FIXED);
 if(!FIXED)assert(!pthread_join(b,NULL));
 release_a=1;assert(!pthread_cond_broadcast(&changed));assert(!pthread_mutex_unlock(&control));
 assert(!pthread_join(a,NULL));if(FIXED)assert(!pthread_join(b,NULL));assert_unlocked();
 assert(flash==(FIXED?2:1));
 schedule=0;identity=0;writes=0;flash=ram=3;
 assert(!nvram_commit());assert(writes==0);assert_unlocked();
 generate_error=-EINVAL;assert(nvram_commit()==-EINVAL);assert_unlocked();generate_error=0;
 ram=4;write_error=-EIO;assert(nvram_commit()==-EIO);assert(flash==3);assert_unlocked();write_error=0;
 alloc_count=0;alloc_fail=1;assert(nvram_commit()==-ENOMEM);assert_unlocked();
 alloc_count=0;alloc_fail=2;assert(!nvram_commit());assert(flash==4);assert_unlocked();
 puts(FIXED?"PASS fixed: commit mutex precedes snapshot; concurrent snapshot blocked; error/unchanged/allocation paths release locks":"PASS baseline counterexample: newer commit snapshots before earlier commit obtains flash serialization");
 return 0;
}
