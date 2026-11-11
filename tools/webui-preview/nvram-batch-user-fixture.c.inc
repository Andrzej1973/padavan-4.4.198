/* Host substitutions for privileged copy boundary; no kernel claims. */
#define __user
#define CAP_SYS_ADMIN 21
#define GFP_KERNEL 0
static int nvram_major=1,authorized=1,copy_calls,copy_fault,copy_alloc_fault,mutate_user;
static int capable(int cap){assert(cap==CAP_SYS_ADMIN);return authorized;}
static void *kzalloc(size_t bytes,int mode)
{(void)mode;assert(bytes==5264&&!user_owned);if(copy_alloc_fault)return NULL;return user_owned=calloc(1,bytes);}
static unsigned long copy_from_user(void *to,const void *from,unsigned long bytes)
{
 copy_calls++;if(copy_fault){memcpy(to,from,bytes/2);return bytes-bytes/2;}
 memcpy(to,from,bytes);
 if(mutate_user)strcpy(((struct wr_nvram_wire_request *)from)->items[0].value,"raced-user-value");
 return 0;
}
static void memzero_explicit(void *p,size_t bytes)
{volatile unsigned char *cursor=p;while(bytes--)*cursor++=0;}
/* USER_ENTRY */
