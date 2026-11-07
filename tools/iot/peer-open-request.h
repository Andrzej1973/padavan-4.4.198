/* Internal core/NETIF contract, never a user-pointer payload. */
#ifndef WR_IOT_PEER_OPEN_REQUEST_H
#define WR_IOT_PEER_OPEN_REQUEST_H
#define WR_IOT_PEER_OPEN_REQUEST_VERSION 1U
enum wr_iot_peer_open_action {WR_PEER_OPEN_BEGIN=1,WR_PEER_OPEN_START,
 WR_PEER_OPEN_DONE,WR_PEER_OPEN_FAIL,WR_PEER_OPEN_CONFIG_CHECK};
struct wr_iot_peer_open_request {
 unsigned int version,action;
 const void *device;
 unsigned long serial;
};
#endif
