/* Read-only link observation. Interface UP is not VPN connectivity proof. */
static int ej_wr_vpn_profile_observation(int eid,webs_t wp,int argc,char **argv)
{
    unsigned int id;char idarg[8],output[512];const char *args[4];
    (void)eid;
    if (!get_login_safe() || argc!=1 || !wr_vpn_action_id(argv[0],&id))
        return websWrite(wp,"{\"interface_state\":\"unknown\"}");
    snprintf(idarg,sizeof(idarg),"%u",id);
    args[0]=WR_VPN_PROFILE_BIN;args[1]="observe";args[2]=idarg;args[3]=NULL;
    if (!wr_vpn_web_run(args,output,sizeof(output)))
        return websWrite(wp,"{\"interface_state\":\"unknown\"}");
    /* The fixed manager emits only bounded metadata for observe, no config. */
    return websWrite(wp,"%s",output);
}
