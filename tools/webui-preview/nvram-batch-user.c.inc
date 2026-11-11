/* Isolated candidate callable body: no exported symbol or production hook.
 * Generic NVRAM writes require system administration, not network-only rights.
 */
long wr_nvram_user_batch(const void __user *user_request)
{
 struct wr_nvram_wire_request *owned;
 struct wr_nvram_edit edits[WR_NVRAM_BATCH_MAX];
 int count,result;
 if(!capable(CAP_SYS_ADMIN))return -EPERM;
 if(nvram_major<0)return -EAGAIN;
 owned=kzalloc(sizeof(*owned),GFP_KERNEL);
 if(!owned)return -ENOMEM;
 /* Copy once; partial-copy failures must also wipe any copied key material. */
 if(copy_from_user(owned,user_request,sizeof(*owned))){result=-EFAULT;goto done;}
 count=wr_nvram_decode_batch(owned,sizeof(*owned),edits);
 if(count<0){result=count;goto done;}
 result=wr_nvram_batch_candidate(edits,(unsigned int)count);
done:
 memzero_explicit(edits,sizeof(edits));
 memzero_explicit(owned,sizeof(*owned));
 kfree(owned);
 return result;
}
