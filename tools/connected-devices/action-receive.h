#ifndef WR_ACTION_RECEIVE_H
#define WR_ACTION_RECEIVE_H
#include "action-wire.h"
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <errno.h>
/* Caller owns a nonblocking local datagram socket with SO_PASSCRED enabled.
 * The expected PID must come from verified service ownership, not the packet.
 * PID birth/session validation remains the caller's responsibility. */
static inline int wr_action_receive(int fd,pid_t expected_pid,uid_t expected_uid,
 struct wr_action_event *out){
 unsigned char packet[WR_ACTION_WIRE_SIZE];
 union {struct cmsghdr alignment;unsigned char bytes[CMSG_SPACE(sizeof(struct ucred))];} control;
 struct iovec io;struct msghdr msg;struct cmsghdr *c;struct ucred peer;ssize_t n;int found=0;
 if(fd<0||expected_pid<=0||!out)return -1;
 memset(&msg,0,sizeof(msg));memset(&control,0,sizeof(control));
 io.iov_base=packet;io.iov_len=sizeof(packet);msg.msg_iov=&io;msg.msg_iovlen=1;msg.msg_control=control.bytes;msg.msg_controllen=sizeof(control);
 n=recvmsg(fd,&msg,MSG_DONTWAIT);
 if(n<0)return errno==EAGAIN||errno==EWOULDBLOCK?0:-1;
 if(n!=WR_ACTION_WIRE_SIZE||(msg.msg_flags&(MSG_TRUNC|MSG_CTRUNC)))return -1;
 for(c=CMSG_FIRSTHDR(&msg);c;c=CMSG_NXTHDR(&msg,c)){
  if(c->cmsg_level!=SOL_SOCKET||c->cmsg_type!=SCM_CREDENTIALS||c->cmsg_len!=CMSG_LEN(sizeof(peer))||found)return -1;
  memcpy(&peer,CMSG_DATA(c),sizeof(peer));found=1;
 }
 if(!found||peer.pid!=expected_pid||peer.uid!=expected_uid)return -1;
 return wr_action_decode(packet,sizeof(packet),out)?1:-1;
}
#endif
