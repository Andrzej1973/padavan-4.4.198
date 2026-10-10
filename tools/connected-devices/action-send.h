#ifndef WR_ACTION_SEND_H
#define WR_ACTION_SEND_H
#include "action-wire.h"
#include <sys/socket.h>
#include <errno.h>
/* Caller supplies an owned connected local datagram FD. Never let reporting
 * block steering or overwrite errno from the actual command. */
static inline int wr_action_send(int fd,const struct wr_action_event *e){
 unsigned char packet[WR_ACTION_WIRE_SIZE];int saved=errno,ok=0;ssize_t n;
 if(fd>=0&&wr_action_encode(e,packet,sizeof(packet))){
  n=send(fd,packet,sizeof(packet),MSG_DONTWAIT|MSG_NOSIGNAL);ok=n==(ssize_t)sizeof(packet);
 }
 errno=saved;return ok;
}
#endif
