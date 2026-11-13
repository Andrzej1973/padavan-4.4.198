#ifndef WR_IOT_STATUS_ENDPOINT_H
#define WR_IOT_STATUS_ENDPOINT_H
#include <sys/types.h>
#include "status-channel.h"
struct wr_iot_status_endpoint {
 int directory,listener,connection;
 pid_t owner;uid_t uid;
 dev_t device;ino_t inode;
 dev_t directory_device,listener_device,connection_device;
 ino_t directory_inode,listener_inode,connection_inode;
 unsigned long long expires;
 char path[108];
};
void wr_iot_status_endpoint_init(struct wr_iot_status_endpoint *);
/* Directory must already be private0700 and owned by uid. Fixed internal path,
 * never HTTP input. Existing socket/file is refused, never unlinked as stale. */
int wr_iot_status_endpoint_listen(struct wr_iot_status_endpoint *,const char *,uid_t);
/* One nonblocking accept/serve step; at most one retained client, expires1s.
 * Caller schedules progress; return1 means response sent, possibly refusal. */
/* Only return a descriptor whose original socket identity is still held. */
int wr_iot_status_endpoint_ready_fd(struct wr_iot_status_endpoint *);
int wr_iot_status_endpoint_step(struct wr_iot_status_endpoint *,int (*)(const struct wr_iot_control_result *));
/* Close/remove only this process's originally bound socket inode. */
int wr_iot_status_endpoint_close(struct wr_iot_status_endpoint *);
int wr_iot_status_endpoint_query(const char *,pid_t,uid_t,const struct wr_iot_control_result *);
#endif
