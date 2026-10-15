/* Never opens the real NVRAM device. All getters model disabled master. */
char *nvram_get(const char *name)
{
    (void)name;
    return "0";
}
