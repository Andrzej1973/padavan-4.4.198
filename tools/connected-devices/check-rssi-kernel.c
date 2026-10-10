#include "rssi-kernel.h"
#include "rssi-query-handler.h"
/* Compile only, never loaded. Exercise all inline wrappers with real headers. */
int wr_rssi_kernel_compile_probe(struct wr_rssi_kernel *observer,
 struct wr_rssi_record *record,struct wr_rssi_snapshot_meta *meta)
{
 int result;
 struct wr_rssi_query_request query={0};
 query.capacity=1;
 wr_rssi_kernel_init(observer);
 result=wr_rssi_kernel_begin(observer,record);
 result+=wr_rssi_kernel_append(observer,record);
 result+=wr_rssi_kernel_snapshot(observer,0,record,1,meta);
 result+=wr_rssi_kernel_query(observer,&query,record,meta);
 return result+(meta->session[0]==observer->session[0] &&
                meta->session[1]==observer->session[1]);
}

int wr_rssi_query_handler_compile_probe(struct wr_rssi_kernel *observer,
 void __user *user,unsigned int capacity,unsigned int *written)
{
 return wr_rssi_query_handle(observer,0,user,capacity,written);
}
