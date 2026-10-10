#ifndef WR_RSSI_QUERY_HANDLER_H
#define WR_RSSI_QUERY_HANDLER_H
#include <linux/capability.h>
#include <linux/errno.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include "rssi-kernel.h"
#include "rssi-query-response.h"
struct wr_rssi_query_buffer {
 struct wr_rssi_record records[64];
 struct wr_rssi_snapshot_meta meta;
 unsigned char encoded[WR_RSSI_QUERY_RESPONSE_MAX_BYTES];
};
/* Caller retains the adapter lifetime through synchronous WEXT dispatch.
 * No adapter pointer is retained and no deferred work is scheduled. */
static inline int wr_rssi_query_handle(struct wr_rssi_kernel *observer,
 unsigned int radio,void __user *user,unsigned int capacity,unsigned int *written)
{
 unsigned char bytes[40];struct wr_rssi_query_request request;
 struct wr_rssi_query_buffer *buffer;int count,result;unsigned int size;
 if(!capable(CAP_NET_ADMIN))return -EPERM;
 if(!observer||!user||!written||radio>1||capacity<40||
    capacity>WR_RSSI_QUERY_RESPONSE_MAX_BYTES)return -EINVAL;
 if(copy_from_user(bytes,user,sizeof bytes))return -EFAULT;
 if(!wr_rssi_query_decode(bytes,sizeof bytes,&request)||request.radio!=radio||
    capacity<48+request.capacity*32)return -EINVAL;
 buffer=kzalloc(sizeof *buffer,GFP_KERNEL);if(!buffer)return -ENOMEM;
 count=wr_rssi_kernel_query(observer,&request,buffer->records,&buffer->meta);
 if(count<0){result=count==-2?-ESTALE:-EINVAL;goto done;}
 size=wr_rssi_query_response_encode(buffer->encoded,sizeof buffer->encoded,
      buffer->meta.session,buffer->meta.sequence,buffer->meta.overwritten,
      radio,buffer->records,(unsigned int)count);
 if(!size){result=-EINVAL;goto done;}
 if(copy_to_user(user,buffer->encoded,size)){result=-EFAULT;goto done;}
 *written=size;result=0;
 done:
 kfree(buffer);return result;
}
#endif
