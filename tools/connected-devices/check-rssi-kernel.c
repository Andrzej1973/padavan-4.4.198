#include "rssi-kernel.h"
/* Compile only, never loaded. Exercise all inline wrappers with real headers. */
int wr_rssi_kernel_compile_probe(struct wr_rssi_kernel *observer,
 struct wr_rssi_record *record,struct wr_rssi_snapshot_meta *meta)
{
 int result;
 wr_rssi_kernel_init(observer);
 result=wr_rssi_kernel_append(observer,record);
 return result+wr_rssi_kernel_snapshot(observer,0,record,1,meta);
}
