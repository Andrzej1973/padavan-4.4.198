/* Linux 4.4 Factory adapter candidate; hardware validation remains pending. */
#include <linux/completion.h>
#include <linux/err.h>
#include <linux/errno.h>
#include <linux/mtd/mtd.h>
#include <linux/math64.h>
#include <linux/mutex.h>
#include <linux/slab.h>
#include <linux/string.h>

static DEFINE_MUTEX(mi_mini_factory_lock);

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
	mutex_lock(&mi_mini_factory_lock);
	result = mtd_read(mtd, offset, length, &returned, buffer);
	mutex_unlock(&mi_mini_factory_lock);
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

static void mi_mini_factory_erase_done(struct erase_info *erase)
{
	complete((struct completion *)erase->priv);
}

/* Single-block EEPROM update; preserve every byte outside the requested range. */
int mi_mini_factory_write(loff_t offset, size_t length,
			  const unsigned char *buffer)
{
	struct mtd_info *mtd;
	struct erase_info erase;
	struct completion erased;
	unsigned char *backup = NULL, *verify = NULL;
	u64 block;
	size_t within, returned;
	int result;

	if (!buffer || !length || offset < 0)
		return -EINVAL;
	mtd = get_mtd_device_nm("Factory");
	if (IS_ERR(mtd))
		return PTR_ERR(mtd);
	if (mtd->type != MTD_NORFLASH || !(mtd->flags & MTD_WRITEABLE) ||
	    !mtd->erasesize || mtd->numeraseregions ||
	    mtd->erasesize > mtd->size || (u64)offset > mtd->size ||
	    length > mtd->size - (u64)offset) {
		result = -EINVAL;
		goto out;
	}
	block = div_u64((u64)offset, mtd->erasesize) * mtd->erasesize;
	within = (size_t)((u64)offset - block);
	if (length > mtd->erasesize - within ||
	    mtd->erasesize > mtd->size - block) {
		result = -EINVAL;
		goto out;
	}
	backup = kmalloc(mtd->erasesize, GFP_KERNEL);
	verify = kmalloc(mtd->erasesize, GFP_KERNEL);
	if (!backup || !verify) {
		result = -ENOMEM;
		goto out;
	}
	mutex_lock(&mi_mini_factory_lock);
	returned = 0;
	result = mtd_read(mtd, block, mtd->erasesize, &returned, backup);
	if (mtd_is_bitflip(result))
		result = 0;
	if (!result && returned != mtd->erasesize)
		result = -EIO;
	if (result)
		goto unlock;
	/* Avoid wear when the requested calibration bytes already match. */
	if (!memcmp(backup + within, buffer, length))
		goto unlock;
	memcpy(backup + within, buffer, length);
	memset(&erase, 0, sizeof(erase));
	init_completion(&erased);
	erase.mtd = mtd;
	erase.addr = block;
	erase.len = mtd->erasesize;
	erase.callback = mi_mini_factory_erase_done;
	erase.priv = (unsigned long)&erased;
	result = mtd_erase(mtd, &erase);
	if (result)
		goto unlock;
	/* Linux 4.4 MTD requires waiting for the completion callback. */
	wait_for_completion(&erased);
	if (erase.state != MTD_ERASE_DONE) {
		result = -EIO;
		goto unlock;
	}
	returned = 0;
	result = mtd_write(mtd, block, mtd->erasesize, &returned, backup);
	if (!result && returned != mtd->erasesize)
		result = -EIO;
	if (result)
		goto unlock;
	returned = 0;
	result = mtd_read(mtd, block, mtd->erasesize, &returned, verify);
	if (mtd_is_bitflip(result))
		result = 0;
	if (!result && (returned != mtd->erasesize ||
		       memcmp(backup, verify, mtd->erasesize)))
		result = -EIO;
unlock:
	mutex_unlock(&mi_mini_factory_lock);
out:
	kfree(verify);
	kfree(backup);
	put_mtd_device(mtd);
	return result;
}
