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
 reset_store();depth=1;for(i=0;i<ARRAYSIZE(nvram_hash);i++){struct nvram_tuple *t=nvram_hash[i],*next;while(t){next=t->next;_nvram_free(t);t=next;}nvram_hash[i]=NULL;}depth=0;assert(!live);
 puts("PASS actual NVRAM allocator/hash + batch prototype: 4/16-key allocation faults preserve old state, colliding bucket replacement, CAS/no-op/space/input/new-key/check-only, borrowed old value retained; host lock/heap substitutes, no ioctl/kernel acceptance");return 0;
}
