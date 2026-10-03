/* Linux 4.4 MTD read adapter candidate; not yet linked into the driver. */
#include <linux/err.h>
#include <linux/errno.h>
#include <linux/mtd/mtd.h>
#include <linux/string.h>

/* offset is relative to Factory, never an absolute flash address. */
int mi_mini_factory_read(loff_t offset, size_t length, unsigned char *buffer)
{
	struct mtd_info *mtd;
	size_t returned = 0;
	int result;

	if (!buffer || !length || offset < 0)
		return -EINVAL;
	mtd = get_mtd_device_nm("Factory");
	if (IS_ERR(mtd))
		return PTR_ERR(mtd);
	if ((u64)offset > mtd->size || length > mtd->size - (u64)offset) {
		result = -EINVAL;
		goto out;
	}
	result = mtd_read(mtd, offset, length, &returned, buffer);
	/* Correctable bitflips return valid data; other read errors are fatal. */
	if (mtd_is_bitflip(result))
		result = 0;
	if (!result && returned != length)
		result = -EIO;
	if (result)
		memset(buffer, 0, length);
out:
	put_mtd_device(mtd);
	return result;
}
