/* Pinned SDK c25283e, native getall source fixture; not kernel code installed by IoT. */
#include <linux/string.h>
int
_nvram_getall(char *buf, int count, int include_temp)
{
	uint i;
	struct nvram_tuple *t;
	int len = 0;

	/* Write name=value\0 ... \0\0 */
	for (i = 0; i < ARRAYSIZE(nvram_hash); i++) {
		for (t = nvram_hash[i]; t; t = t->next) {
			if (!include_temp && t->val_tmp)
				continue;
			if ((count - len) > (strlen(t->name) + 1 + strlen(t->value) + 1))
				len += sprintf(buf + len, "%s=%s", t->name, t->value) + 1;
			else
				break;
		}
	}

	return 0;
}

int
_nvram_generate(struct nvram_header *header, int rehash)
{
	int i;
	char *ptr, *end;
	struct nvram_tuple *t;
	uint8_t crc;

	/* Generate header */
	header->magic = NVRAM_MAGIC;
	header->crc_ver_init = (NVRAM_VERSION << 8);
	header->crc_ver_init |= (SDRAM_INIT << 16);
	header->config_refresh = SDRAM_CONFIG;
	header->config_refresh |= (SDRAM_REFRESH << 16);
	header->config_ncdl = 0;

	/* Pointer to data area */
	ptr = (char *)header + sizeof(struct nvram_header);

	/* Leave space for a double NUL at the end */
	end = (char *)header + NVRAM_SPACE - 2;

	/* Write out all tuples */
	for (i = 0; i < ARRAYSIZE(nvram_hash); i++) {
		for (t = nvram_hash[i]; t; t = t->next) {
			if (!rehash && t->val_tmp)
				continue;
			if ((ptr + strlen(t->name) + 1 + strlen(t->value) + 1) > end)
				break;
			ptr += sprintf(ptr, "%s=%s", t->name, t->value) + 1;
		}
	}

	/* End with a double NULL */
	ptr += 1;

	/* Set new length */
	header->len = ROUNDUP(ptr - (char *) header, 4);

	/* Fill residual by 0xFF */
	if (header->len < NVRAM_SPACE)
		memset((char *)header + header->len, 0xFF, NVRAM_SPACE - header->len);

	crc = nvram_calc_crc(header);

	/* Set new CRC8 */
	header->crc_ver_init |= crc;

	/* Reinitialize hash table */
	if (rehash) {
		nvram_free();
		nvram_rehash(header);
	}

	return 0;
}
