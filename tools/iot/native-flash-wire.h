/* Linux native ABI only; uses the existing anvram_ioctl_t layout.
 * READ_FLASH accepts only size=sizeof(anvram_ioctl_t), is_temp=0,
 * len_param=0, param=NULL, len_value=NVRAM_SPACE and a non-NULL value.
 * Returns fixed native NVRAM bytes from Config/NVRAM_MTD_OFFSET under
 * nvram_sem, never RAM GETALL. Requires CAP_SYS_ADMIN. No writes.
 * An error may leave a partially copied user buffer; discard it completely.
 */
#ifndef WR_NVRAM_FLASH_READBACK_WIRE_H
#define WR_NVRAM_FLASH_READBACK_WIRE_H
#define WR_NVRAM_IOCTL_READ_FLASH 50
#endif
