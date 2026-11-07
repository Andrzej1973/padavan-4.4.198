/* Linux getrandom(GRND_NONBLOCK): no predictable/uninitialized fallback and
 * no early-boot wait. Kernel 4.4 refuses until nonblocking pool initialized.
 * Caller treats failure as unavailable reservation, never as permission to
 * expose an open BSS or to substitute a fixed key. No credentials are saved. */
#ifndef WR_IOT_PRECREATED_ENTROPY_H
#define WR_IOT_PRECREATED_ENTROPY_H
#include <unistd.h>
#include <sys/syscall.h>
#include <errno.h>
#ifndef WR_IOT_GETRANDOM
#if defined(SYS_getrandom)
#define WR_IOT_GETRANDOM(buf,n,flags) syscall(SYS_getrandom,buf,n,flags)
#elif defined(__NR_getrandom)
#define WR_IOT_GETRANDOM(buf,n,flags) syscall(__NR_getrandom,buf,n,flags)
#endif
#endif
static inline int wr_iot_precreated_entropy(void *context,unsigned char *bytes,
 unsigned int length)
{
 (void)context;
 if(!bytes||length!=32)return -1;
#ifdef WR_IOT_GETRANDOM
 /* GRND_NONBLOCK is 1 in this pinned kernel's UAPI. No GRND_RANDOM flag. */
 return (int)WR_IOT_GETRANDOM(bytes,length,1U);
#else
 /* Old libc headers are not permission to guess an architecture syscall ID. */
 errno=ENOSYS;return -1;
#endif
}
#endif
