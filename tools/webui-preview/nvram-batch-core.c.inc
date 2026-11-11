/* Isolated kernel-context prototype, not installed or exposed by an ioctl.
 * Inputs must be immutable kernel-owned strings. Existing nvram_lock protects
 * compare, allocation/staging and publication. No compaction/flash/notification.
 */
#define WR_NVRAM_BATCH_MAX 16
#define WR_NVRAM_BATCH_CHECK 1U
#define WR_NVRAM_BATCH_SET 2U
#define WR_NVRAM_BATCH_VALUE_MAX 128U
struct wr_nvram_edit {const char *name,*expected,*value;unsigned int flags;};
static struct nvram_tuple *wr_nvram_find(const char *name)
{
 struct nvram_tuple *t;
 for(t=nvram_hash[hash(name)%ARRAYSIZE(nvram_hash)];t&&strcmp(t->name,name);t=t->next);
 return t;
}
static int wr_nvram_batch_candidate(const struct wr_nvram_edit *items,unsigned int count)
{
 struct nvram_tuple *staged[WR_NVRAM_BATCH_MAX]={0},*old,**link;
 unsigned int i,j,index,changed=0;
 unsigned long flags,checkpoint,need=0;
 int ret=0;
 if(!items||!count||count>WR_NVRAM_BATCH_MAX)return -EINVAL;
 for(i=0;i<count;i++){
  if(!items[i].name||!items[i].name[0]||strnlen(items[i].name,NVRAM_MAX_PARAM_LEN)>=NVRAM_MAX_PARAM_LEN||
     !items[i].flags||(items[i].flags&~3U))return -EINVAL;
  if(items[i].flags&WR_NVRAM_BATCH_CHECK){
   if(!items[i].expected||strnlen(items[i].expected,WR_NVRAM_BATCH_VALUE_MAX+1)>WR_NVRAM_BATCH_VALUE_MAX)return -EINVAL;
  }else if(items[i].expected)return -EINVAL;
  if(items[i].flags&WR_NVRAM_BATCH_SET){
   if(!items[i].value||strnlen(items[i].value,WR_NVRAM_BATCH_VALUE_MAX+1)>WR_NVRAM_BATCH_VALUE_MAX)return -EINVAL;
  }else if(items[i].value)return -EINVAL;
  for(j=0;j<i;j++)if(!strcmp(items[i].name,items[j].name))return -EINVAL;
 }
 spin_lock_irqsave(&nvram_lock,flags);
 checkpoint=nvram_offset;
 if(!nvram_values||checkpoint>=NVRAM_VALUES_SPACE){ret=-EIO;goto unlock;}
 for(i=0;i<count;i++){
  old=wr_nvram_find(items[i].name);
  if((items[i].flags&WR_NVRAM_BATCH_CHECK)&&strcmp(old?old->value:"",items[i].expected)){
   ret=-EAGAIN;goto unlock;
  }
  if((items[i].flags&WR_NVRAM_BATCH_SET)&&(!old||old->val_tmp||strcmp(old->value,items[i].value)))
   need+=strlen(items[i].value)+1;
 }
 if(need>=NVRAM_VALUES_SPACE-checkpoint){ret=-ENOSPC;goto unlock;}
 for(i=0;i<count;i++){
  if(!(items[i].flags&WR_NVRAM_BATCH_SET))continue;
  old=wr_nvram_find(items[i].name);
  if(old&&!old->val_tmp&&!strcmp(old->value,items[i].value))continue;
  staged[i]=_nvram_realloc(NULL,items[i].name,items[i].value,0);
  if(!staged[i]){ret=-ENOMEM;goto rollback;}
  changed++;
 }
 /* All failure points precede this loop. Re-find links to handle collisions
  * and replacement of an earlier predecessor in the same bucket. */
 for(i=0;i<count;i++){
  if(!staged[i])continue;
  index=hash(items[i].name)%ARRAYSIZE(nvram_hash);
  for(link=&nvram_hash[index];*link&&strcmp((*link)->name,items[i].name);link=&(*link)->next);
  old=*link;staged[i]->next=old?old->next:NULL;*link=staged[i];
  _nvram_free(old);
 }
 ret=(int)changed;goto unlock;
rollback:
 for(i=0;i<count;i++)_nvram_free(staged[i]);
 /* Clones only appended to unused arena tail; old values were never touched. */
 memset(nvram_values+checkpoint,0,nvram_offset-checkpoint);nvram_offset=checkpoint;
unlock:
 spin_unlock_irqrestore(&nvram_lock,flags);
 return ret;
}
