/* Candidate Linux userspace adapter; caller owns the request and its wiping.
 * A successful return describes RAM publication only, never flash or radio.
 */
#ifndef WR_NVRAM_BATCH_CLIENT_H
#define WR_NVRAM_BATCH_CLIENT_H
#include <errno.h>
#include <sys/ioctl.h>
#include "nvram-batch-wire.h"
#ifndef WR_NVRAM_IOCTL_CALL
#define WR_NVRAM_IOCTL_CALL ioctl
#endif
static inline int wr_nvram_submit_batch(int fd,const struct wr_nvram_wire_request *request,
                                       unsigned int *changed)
{
 int result;
 if(fd<0||!request||!changed||request->version!=WR_NVRAM_WIRE_VERSION||
    !request->count||request->count>WR_NVRAM_WIRE_COUNT){errno=EINVAL;return -1;}
 /* Exactly one attempt, including EINTR/old-kernel errors. Never fall back
  * to sequential SETs: they cannot preserve the all-or-nothing guarantee. */
 result=WR_NVRAM_IOCTL_CALL(fd,WR_NVRAM_IOCTL_BATCH_V1,request);
 if(result<0)return -1;
 if((unsigned int)result>request->count){errno=EPROTO;return -1;}
 *changed=(unsigned int)result;
 return 0;
}
#endif
