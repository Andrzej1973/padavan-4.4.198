static int client_calls,client_errno,client_result;
static const void *client_request;
static int mock_batch_ioctl(int fd,unsigned long command,const void *request)
{
 assert(fd==7&&command==WR_NVRAM_IOCTL_BATCH_V1&&request==client_request);
 client_calls++;errno=client_errno;return client_result;
}
#define WR_NVRAM_IOCTL_CALL mock_batch_ioctl
#include "nvram-batch-client.h"
static const char *names[]={"rt_guest_ssid","rt_guest_enable","rt_guest_crypto","rt_guest_date_x"};
static void reset_store(void)
{
 unsigned int i;struct nvram_tuple *t,*next;
 assert(!depth);depth=1;
 for(i=0;i<ARRAYSIZE(nvram_hash);i++){for(t=nvram_hash[i];t;t=next){next=t->next;_nvram_free(t);}nvram_hash[i]=NULL;}
 assert(!live);memset(arena,0,sizeof(arena));nvram_offset=0;allocations=fail_at=0;
 for(i=0;i<4;i++)assert(!_nvram_set(names[i],"before",0));
 depth=0;allocations=0;
}
static pthread_barrier_t start_barrier;
struct competing_write {const char *value;int legacy,result;};
static void *compete(void *opaque)
{
 struct competing_write *w=opaque;unsigned long flags;
 struct wr_nvram_edit request[4];unsigned int i;
 for(i=0;i<4;i++)request[i]=(struct wr_nvram_edit){names[i],"before",w->value,3};
 int barrier_result=pthread_barrier_wait(&start_barrier);
 assert(barrier_result==0||barrier_result==PTHREAD_BARRIER_SERIAL_THREAD);
 if(w->legacy){
  spin_lock_irqsave(&nvram_lock,flags);
  w->result=_nvram_set(names[0],w->value,0);
  spin_unlock_irqrestore(&nvram_lock,flags);
 }else w->result=wr_nvram_batch_candidate(request,4);
 return NULL;
}
static void concurrent_cases(void)
{
 for(int legacy=0;legacy<=1;legacy++)for(int trial=0;trial<100;trial++){
  pthread_t threads[2];struct competing_write a={"batch-A",0,99},b={"writer-B",legacy,99};
  reset_store();assert(!pthread_barrier_init(&start_barrier,NULL,2));
  assert(!pthread_create(&threads[0],NULL,compete,&a));
  assert(!pthread_create(&threads[1],NULL,compete,&b));
  assert(!pthread_join(threads[0],NULL));assert(!pthread_join(threads[1],NULL));
  assert(!pthread_barrier_destroy(&start_barrier));assert(!depth);
  if(!legacy){
   assert((a.result==4&&b.result==-EAGAIN)||(a.result==-EAGAIN&&b.result==4));
   const char *winner=a.result==4?a.value:b.value;
   for(unsigned int i=0;i<4;i++)assert(!strcmp(_nvram_get(names[i]),winner));
  }else{
   assert(b.result==0&&(a.result==4||a.result==-EAGAIN));
   assert(!strcmp(_nvram_get(names[0]),b.value));
   for(unsigned int i=1;i<4;i++)assert(!strcmp(_nvram_get(names[i]),a.result==4?a.value:"before"));
  }
 }
 puts("PASS 200 synchronized two-writer trials: batch CAS has one winner; legacy single-key writer serializes but can overwrite a completed batch");
}
static void wire_cases(void)
{
 struct wr_nvram_wire_request packet={0},valid;struct wr_nvram_edit decoded[16],sentinel[16];
 memset(decoded,0x5a,sizeof(decoded));memcpy(sentinel,decoded,sizeof(decoded));
 packet.version=1;packet.count=1;packet.items[0].flags=3;
 strcpy(packet.items[0].name,names[0]);strcpy(packet.items[0].expected,"before");strcpy(packet.items[0].value,"wire-after");
 valid=packet;
 for(int fault=0;fault<10;fault++){
  packet=valid;
  switch(fault){
   case 0:packet.version=2;break;
   case 1:packet.count=17;break;
   case 2:packet.reserved[0]=1;break;
   case 3:packet.items[1].flags=1;break;
   case 4:packet.items[0].reserved[1]=1;break;
   case 5:memset(packet.items[0].name,'x',64);break;
   case 6:packet.items[0].value[128]='x';break;
   case 7:packet.items[0].flags=1;break;
   case 8:packet.count=2;packet.items[1]=packet.items[0];break;
   case 9:packet.items[0].name[0]='=';break;
  }
  assert(wr_nvram_decode_batch(&packet,sizeof(packet),decoded)==-EINVAL);
  assert(!memcmp(decoded,sentinel,sizeof(decoded)));
 }
 assert(wr_nvram_decode_batch(&valid,sizeof(valid)-1,decoded)==-EINVAL);
 assert(wr_nvram_decode_batch(&valid,sizeof(valid)+1,decoded)==-EINVAL);
 assert(!memcmp(decoded,sentinel,sizeof(decoded)));
 packet=valid;reset_store();assert(wr_nvram_decode_batch(&packet,sizeof(packet),decoded)==1);
 assert(wr_nvram_batch_candidate(decoded,packet.count)==1);
 assert(!strcmp(_nvram_get(names[0]),"wire-after"));
 puts("PASS fixed5264-byte pointer-free request: malformed buffers leave output untouched; decoded request executes actual batch core");
}
static void user_copy_cases(void)
{
 struct wr_nvram_wire_request packet={0};
 packet.version=1;packet.count=1;packet.items[0].flags=3;
 strcpy(packet.items[0].name,names[0]);strcpy(packet.items[0].expected,"before");strcpy(packet.items[0].value,"owned-value");
 reset_store();authorized=0;assert(wr_nvram_user_batch(&packet)==-EPERM);assert(!copy_calls&&!user_owned);
 authorized=1;nvram_major=-1;assert(wr_nvram_user_batch(&packet)==-EAGAIN);assert(!copy_calls&&!user_owned);nvram_major=1;
 copy_alloc_fault=1;assert(wr_nvram_user_batch(&packet)==-ENOMEM);assert(!copy_calls&&!user_owned);copy_alloc_fault=0;
 copy_fault=1;assert(wr_nvram_user_batch(&packet)==-EFAULT);assert(user_frees==1&&!user_owned);copy_fault=0;
 assert(!strcmp(_nvram_get(names[0]),"before"));
 packet.version=2;assert(wr_nvram_user_batch(&packet)==-EINVAL);assert(user_frees==2&&!user_owned);packet.version=1;
 mutate_user=1;assert(wr_nvram_user_batch(&packet)==1);mutate_user=0;
 assert(!strcmp(_nvram_get(names[0]),"owned-value"));
 assert(!strcmp(packet.items[0].value,"raced-user-value"));assert(user_frees==3&&!user_owned);
 assert(wr_nvram_user_batch(&packet)==-EAGAIN);assert(user_frees==4&&!user_owned);
 assert(dev_nvram_ioctl(NULL,NVRAM_IOCTL_COMMIT,0)==71);
 assert(dev_nvram_ioctl(NULL,NVRAM_IOCTL_CLEAR,0)==72);
 assert(dev_nvram_ioctl(NULL,NVRAM_IOCTL_SET,0)==73);
 assert(dev_nvram_ioctl(NULL,NVRAM_IOCTL_GET,0)==74);assert(legacy_calls==4);
 assert(dev_nvram_ioctl(NULL,0xffffffffU,0)==-EINVAL);
 reset_store();authorized=0;
 assert(dev_nvram_ioctl(NULL,WR_NVRAM_IOCTL_BATCH_V1,(unsigned long)&packet)==-EPERM);
 authorized=1;assert(dev_nvram_ioctl(NULL,WR_NVRAM_IOCTL_BATCH_V1,(unsigned long)&packet)==1);
 assert(!strcmp(_nvram_get(names[0]),"raced-user-value"));assert(legacy_calls==4);
 puts("PASS actual generated ioctl dispatcher: legacy four commands unchanged, unknown command rejected, new command enforces permission and reaches owned batch");
 puts("PASS actual user-entry body with host substitutes: permission/startup/ENOMEM, partial-copy EFAULT, invalid/stale requests, immutable owned copy and wipe before every free");
}
static void client_cases(void)
{
 struct wr_nvram_wire_request packet={0};unsigned int result=99;
 int errors[]={EINVAL,ENOTTY,EPERM,EAGAIN,EFAULT,ENOMEM,ENOSPC,EIO,EINTR};
 packet.version=1;packet.count=1;client_request=&packet;
 for(unsigned int i=0;i<ARRAYSIZE(errors);i++){
  client_errno=errors[i];client_result=-1;int before=client_calls;
  assert(wr_nvram_submit_batch(7,&packet,&result)==-1);
  assert(errno==errors[i]&&client_calls==before+1&&result==99);
 }
 client_result=2;assert(wr_nvram_submit_batch(7,&packet,&result)==-1&&errno==EPROTO&&result==99);
 client_result=0;assert(!wr_nvram_submit_batch(7,&packet,&result)&&result==0);
 client_result=1;assert(!wr_nvram_submit_batch(7,&packet,&result)&&result==1);
 int before=client_calls;packet.version=2;
 assert(wr_nvram_submit_batch(7,&packet,&result)==-1&&errno==EINVAL&&result==1&&client_calls==before);
 puts("PASS actual client adapter: one ioctl attempt per error including EINTR/unsupported kernel, no fallback/retry, output unchanged on errors, bounded success");
}
int main(void)
{
 struct wr_nvram_edit edits[4];unsigned int i;unsigned long before;int old_live;
 for(i=0;i<4;i++)edits[i]=(struct wr_nvram_edit){names[i],"before","after-atomic",3};
 /* Every actual allocator failure must preserve all old keys and arena offset. */
 for(int fault=1;fault<=4;fault++){
  reset_store();before=nvram_offset;old_live=live;fail_at=fault;
  assert(wr_nvram_batch_candidate(edits,4)==-ENOMEM);assert(!depth&&live==old_live&&nvram_offset==before);
  for(i=0;i<4;i++)assert(!strcmp(_nvram_get(names[i]),"before"));
 }
 reset_store();const char *borrowed=_nvram_get(names[0]);
 assert(wr_nvram_batch_candidate(edits,4)==4);assert(!depth&&!strcmp(borrowed,"before"));
 for(i=0;i<4;i++)assert(!strcmp(_nvram_get(names[i]),"after-atomic"));
 before=nvram_offset;allocations=0;
 assert(wr_nvram_batch_candidate(edits,4)==-EAGAIN);assert(!allocations&&nvram_offset==before);
 for(i=0;i<4;i++)edits[i].expected="after-atomic";
 assert(wr_nvram_batch_candidate(edits,4)==0);assert(!allocations&&nvram_offset==before);
 reset_store();before=nvram_offset;nvram_offset=NVRAM_VALUES_SPACE-1;old_live=live;
 for(i=0;i<4;i++)edits[i].expected="before";
 assert(wr_nvram_batch_candidate(edits,4)==-ENOSPC);assert(!depth&&live==old_live&&nvram_offset==NVRAM_VALUES_SPACE-1);
 for(i=0;i<4;i++)assert(!strcmp(_nvram_get(names[i]),"before"));
 nvram_offset=before;
 edits[1].name=edits[0].name;assert(wr_nvram_batch_candidate(edits,4)==-EINVAL);edits[1].name=names[1];
 assert(wr_nvram_batch_candidate(NULL,4)==-EINVAL);assert(wr_nvram_batch_candidate(edits,0)==-EINVAL);
 assert(wr_nvram_batch_candidate(edits,17)==-EINVAL);
 /* Read-only expected key and a newly inserted key share one locked decision. */
 struct wr_nvram_edit pair[]={{names[0],"before",NULL,1},{"wl_guest_ssid","","new",3}};
 assert(wr_nvram_batch_candidate(pair,2)==1);assert(!strcmp(_nvram_get(names[0]),"before")&&!strcmp(_nvram_get("wl_guest_ssid"),"new"));
 /* A full batch deliberately shares one hash bucket: replacement must not
  * lose links when an earlier item replaces another item's predecessor. */
 char collision_names[16][32];struct wr_nvram_edit full[16];unsigned int found=0;
 for(unsigned int candidate=0;found<16;candidate++){
  char name[32];snprintf(name,sizeof(name),"collision_%u",candidate);
  if(hash(name)%ARRAYSIZE(nvram_hash)==0){
   strcpy(collision_names[found],name);
   full[found]=(struct wr_nvram_edit){collision_names[found],"before","collision-after",3};found++;
  }
 }
 for(int fault=1;fault<=16;fault++){
  reset_store();depth=1;
  for(i=0;i<16;i++)assert(!_nvram_set(full[i].name,"before",0));
  depth=0;allocations=0;fail_at=fault;before=nvram_offset;old_live=live;
  assert(wr_nvram_batch_candidate(full,16)==-ENOMEM);
  assert(!depth&&live==old_live&&nvram_offset==before);
  for(i=0;i<16;i++)assert(!strcmp(_nvram_get(full[i].name),"before"));
 }
 fail_at=0;allocations=0;assert(wr_nvram_batch_candidate(full,16)==16);
 for(i=0;i<16;i++)assert(!strcmp(_nvram_get(full[i].name),"collision-after"));
 concurrent_cases();wire_cases();user_copy_cases();client_cases();
 reset_store();depth=1;for(i=0;i<ARRAYSIZE(nvram_hash);i++){struct nvram_tuple *t=nvram_hash[i],*next;while(t){next=t->next;_nvram_free(t);t=next;}nvram_hash[i]=NULL;}depth=0;assert(!live);
 puts("PASS actual NVRAM allocator/hash + batch prototype: 4/16-key allocation faults preserve old state, colliding bucket replacement, CAS/no-op/space/input/new-key/check-only, borrowed old value retained; host lock/heap substitutes, no ioctl/kernel acceptance");return 0;
}
