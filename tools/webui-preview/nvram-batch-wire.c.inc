/* Decode only an immutable, kernel-owned copy; outputs borrow that copy.
 * This function performs no user access, allocation, writes or logging. */
static int wr_nvram_zero_bytes(const void *data,unsigned int size)
{
 const unsigned char *bytes=data;unsigned int i;
 for(i=0;i<size;i++)if(bytes[i])return 0;
 return 1;
}
static int wr_nvram_canonical_string(const char *value,unsigned int size)
{
 unsigned int length=strnlen(value,size);
 return length<size&&wr_nvram_zero_bytes(value+length,size-length);
}
int wr_nvram_decode_batch(const struct wr_nvram_wire_request *request,
                         unsigned int bytes,struct wr_nvram_edit *out)
{
 unsigned int i,j;const struct wr_nvram_wire_item *item;
 if(!request||!out||bytes!=sizeof(*request)||sizeof(*request)!=5264U||
    sizeof(struct wr_nvram_wire_item)!=328U)return -EINVAL;
 if(request->version!=WR_NVRAM_WIRE_VERSION||!request->count||
    request->count>WR_NVRAM_WIRE_COUNT||
    !wr_nvram_zero_bytes(request->reserved,sizeof(request->reserved)))return -EINVAL;
 /* Validate the entire buffer before producing any borrowed pointers. */
 for(i=0;i<WR_NVRAM_WIRE_COUNT;i++){
  item=&request->items[i];
  if(i>=request->count){
   if(!wr_nvram_zero_bytes(item,sizeof(*item)))return -EINVAL;
   continue;
  }
  if(!item->flags||(item->flags&~3U)||
     !wr_nvram_zero_bytes(item->reserved,sizeof(item->reserved))||
     !item->name[0]||!wr_nvram_canonical_string(item->name,sizeof(item->name))||
     !wr_nvram_canonical_string(item->expected,sizeof(item->expected))||
     !wr_nvram_canonical_string(item->value,sizeof(item->value)))return -EINVAL;
  for(j=0;item->name[j];j++)
   if((unsigned char)item->name[j]<33U||(unsigned char)item->name[j]>126U||item->name[j]=='=')return -EINVAL;
  if(!(item->flags&WR_NVRAM_BATCH_CHECK)&&item->expected[0])return -EINVAL;
  if(!(item->flags&WR_NVRAM_BATCH_SET)&&item->value[0])return -EINVAL;
  for(j=0;j<i;j++)if(!strcmp(item->name,request->items[j].name))return -EINVAL;
 }
 for(i=0;i<request->count;i++){
  item=&request->items[i];out[i].name=item->name;out[i].flags=item->flags;
  out[i].expected=(item->flags&WR_NVRAM_BATCH_CHECK)?item->expected:NULL;
  out[i].value=(item->flags&WR_NVRAM_BATCH_SET)?item->value:NULL;
 }
 return (int)request->count;
}
