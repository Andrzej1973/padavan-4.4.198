#include "rssi-kernel.h"
/* Compile only, never loaded. Exercise all inline wrappers with real headers. */
int wr_rssi_kernel_compile_probe(struct wr_rssi_kernel *observer,
 struct wr_rssi_record *record,struct wr_rssi_snapshot_meta *meta)
{
 int result;
 wr_rssi_kernel_init(observer);
 result=wr_rssi_kernel_begin(observer,record);
 result+=wr_rssi_kernel_append(observer,record);
 result+=wr_rssi_kernel_snapshot(observer,0,record,1,meta);
 return result+(meta->session[0]==observer->session[0] &&
                meta->session[1]==observer->session[1]);
}
