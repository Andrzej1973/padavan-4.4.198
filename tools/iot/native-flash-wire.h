/* Linux native ABI only; uses the existing anvram_ioctl_t layout.
 * READ_FLASH accepts only size=sizeof(anvram_ioctl_t), is_temp=0,
 * len_param=0, param=NULL, len_value=NVRAM_SPACE and a non-NULL value.
 * Returns fixed native NVRAM bytes from Config/NVRAM_MTD_OFFSET under
 * nvram_sem, never RAM GETALL. READ_FLASH requires CAP_SYS_ADMIN and performs no writes.
 * An error may leave a partially copied user buffer; discard it completely.
 */
#ifndef WR_NVRAM_FLASH_READBACK_WIRE_H
#define WR_NVRAM_FLASH_READBACK_WIRE_H
#define WR_NVRAM_IOCTL_READ_FLASH 50
/* Pointer-free versioned conditional save ABI. Flags 0 = automatic policy,
 * bit 0 = explicitly requested Save. Admission checks native profile and
 * manual policy under the generation spinlock while holding nvram_sem.
 * Return zero requires full native flash readback equality under that mutex.
 * Callers must still verify request ownership/currentness before publication.
 */
#define WR_NVRAM_IOCTL_SAVE_PROFILE 51
#define WR_NVRAM_SAVE_EXPLICIT 1
#define WR_NVRAM_PROFILE_KEY "wr_iot_config_v1"
struct wr_nvram_save_profile {
 unsigned int size,version,flags,record_length;
 char record[384];
};
typedef char wr_nvram_save_profile_abi[
 (sizeof(unsigned int)==4 && sizeof(struct wr_nvram_save_profile)==400)?1:-1];
#endif
