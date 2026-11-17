/* Conditional save linearizes policy/profile admission with native generation.
 * No SET, radio action, arbitrary key or arbitrary MTD target is accepted.
 */
static int
wr_nvram_generated_profile_matches(unsigned char *bytes, const struct wr_nvram_save_profile *request)
{
 struct nvram_header *header = (struct nvram_header *)bytes;
 unsigned char *at = bytes + sizeof(*header), *end, *nul, *eq;
 size_t keylen = sizeof(WR_NVRAM_PROFILE_KEY) - 1;
 if (header->len < sizeof(*header) || header->len > NVRAM_SPACE)
  return 0;
 end = bytes + header->len;
 while (at < end && *at) {
  nul = memchr(at, 0, end - at);
  if (!nul)
   return 0;
  eq = memchr(at, '=', nul - at);
  if (!eq)
   return 0;
  if ((size_t)(eq - at) == keylen && !memcmp(at, WR_NVRAM_PROFILE_KEY, keylen))
   return (size_t)(nul - eq - 1) == request->record_length &&
          !memcmp(eq + 1, request->record, request->record_length);
  at = nul + 1;
 }
 return 0;
}

static long
wr_nvram_user_save_profile(const struct wr_nvram_save_profile __user *user)
{
 struct wr_nvram_save_profile request;
 unsigned char *written = NULL, *readback = NULL;
 volatile unsigned char *wipe;
 const char *current, *policy;
 unsigned long flags;
 size_t i;
 int ret = -EINVAL;
 if (!capable(CAP_SYS_ADMIN))
  return -EPERM;
 memset(&request, 0, sizeof(request));
 if (!user || copy_from_user(&request, user, sizeof(request))) {
  ret = -EFAULT;
  goto done;
 }
 if (request.size != sizeof(request) || request.version != 1 ||
     request.flags > WR_NVRAM_SAVE_EXPLICIT || !request.record_length ||
     request.record_length >= sizeof(request.record) ||
     request.record[request.record_length] ||
     memchr(request.record, 0, request.record_length))
  goto done;
 if (nvram_major < 0) {
  ret = -EAGAIN;
  goto done;
 }
 written = kzalloc(NVRAM_SPACE, GFP_KERNEL);
 readback = kzalloc(NVRAM_SPACE, GFP_KERNEL);
 if (!written || !readback) {
  ret = -ENOMEM;
  goto done;
 }
 mutex_lock(&nvram_sem);
 spin_lock_irqsave(&nvram_lock, flags);
 current = _nvram_get(WR_NVRAM_PROFILE_KEY);
 policy = _nvram_get("nvram_manual");
 if (!current || strcmp(current, request.record))
  ret = -ESTALE;
 else if (policy && *policy && strcmp(policy, "0") && strcmp(policy, "1"))
  ret = -EINVAL;
 else if (!(request.flags & WR_NVRAM_SAVE_EXPLICIT) && policy && !strcmp(policy, "1"))
  ret = -EAGAIN;
 else
  ret = _nvram_generate((struct nvram_header *)written, 0);
 spin_unlock_irqrestore(&nvram_lock, flags);
 if (ret)
  goto unlock;
 /* A temporary-only native tuple is excluded by flash generation. */
 if (!wr_nvram_generated_profile_matches(written, &request)) {
  ret = -ESTALE;
  goto unlock;
 }
 ret = ra_mtd_read_nm(MTD_NVRAM_NAME, NVRAM_MTD_OFFSET, NVRAM_SPACE, readback);
 if (ret)
  goto unlock;
 if (memcmp(written, readback, NVRAM_SPACE)) {
  ret = ra_mtd_write_nm(MTD_NVRAM_NAME, NVRAM_MTD_OFFSET, NVRAM_SPACE, written);
  if (ret)
   goto unlock;
  ret = ra_mtd_read_nm(MTD_NVRAM_NAME, NVRAM_MTD_OFFSET, NVRAM_SPACE, readback);
  if (!ret && memcmp(written, readback, NVRAM_SPACE))
   ret = -EIO;
 }
 unlock:
 mutex_unlock(&nvram_sem);
 if (ret > 0)
  ret = -EIO;
 done:
 if (written) {
  wipe = written;
  for (i = 0; i < NVRAM_SPACE; i++)
   wipe[i] = 0;
  kfree(written);
 }
 if (readback) {
  wipe = readback;
  for (i = 0; i < NVRAM_SPACE; i++)
   wipe[i] = 0;
  kfree(readback);
 }
 wipe = (volatile unsigned char *)&request;
 for (i = 0; i < sizeof(request); i++)
  wipe[i] = 0;
 return ret;
}
