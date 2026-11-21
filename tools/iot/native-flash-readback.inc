/* Privileged fixed-target Linux readback. No arbitrary MTD names or offsets. */
static long
wr_nvram_user_read_flash(anvram_ioctl_t __user *user)
{
 anvram_ioctl_t request;
 unsigned char *buffer;
 volatile unsigned char *wipe;
 size_t i;
 int ret;
 if (!capable(CAP_SYS_ADMIN))
  return -EPERM;
 if (!user || copy_from_user(&request, user, sizeof(request)))
  return -EFAULT;
 if (request.size != sizeof(request) || request.is_temp ||
     request.len_param || request.param || request.len_value != NVRAM_SPACE ||
     !request.value)
  return -EINVAL;
 if (nvram_major < 0)
  return -EAGAIN;
 buffer = kzalloc(NVRAM_SPACE, GFP_KERNEL);
 if (!buffer)
  return -ENOMEM;
 mutex_lock(&nvram_sem);
 ret = ra_mtd_read_nm(MTD_NVRAM_NAME, NVRAM_MTD_OFFSET, NVRAM_SPACE, buffer);
 mutex_unlock(&nvram_sem);
 if (ret) {
  if (ret > 0)
   ret = -EIO;
  goto done;
 }
 if (copy_to_user(request.value, buffer, NVRAM_SPACE))
  ret = -EFAULT;
 done:
 wipe = buffer;
 for (i = 0; i < NVRAM_SPACE; i++)
  wipe[i] = 0;
 kfree(buffer);
 return ret;
}
