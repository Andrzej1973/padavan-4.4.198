#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <netinet/in.h>
#include <linux/ip.h>
#include <linux/if_tunnel.h>

#include "eoip_version.h"
#include "libnetlink.h"
#include "unified/eoip_proto.h"
#include "netlink-query.h"
#ifndef WR_EOIP_QUERY_LINK
#define WR_EOIP_QUERY_LINK wr_eoip_query_link
#endif

// nested attribute table size covering both the system IFLA_GRE_* range
// and the private eoip attributes
#define EOIP_PARSE_MAX (IFLA_GRE_MAX>IFLA_EOIP_ATTR_MAX?IFLA_GRE_MAX:IFLA_EOIP_ATTR_MAX)

// keepalive suffix for the list output; empty against a kernel module
// that predates the keepalive attributes
static void ka_suffix(struct rtattr *ifgreo[],char *kbuf,size_t len) {
	long kai=-1;
	int kar=0;

	kbuf[0]=0;
	if (ifgreo[IFLA_EOIP_KA_INTERVAL])
		kai=rta_getattr_u32(ifgreo[IFLA_EOIP_KA_INTERVAL]);
	if (ifgreo[IFLA_EOIP_KA_RETRIES])
		kar=rta_getattr_u8(ifgreo[IFLA_EOIP_KA_RETRIES]);
	if (kai==0)
		snprintf(kbuf,len," keepalive none");
	else if (kai>0)
		snprintf(kbuf,len," keepalive %ld,%d",kai,kar);
}

int print_link(const struct sockaddr_nl *who __attribute((unused)), struct nlmsghdr *n, void *arg __attribute((unused))) {
	struct ndmsg *r = NLMSG_DATA(n);
	int len = n->nlmsg_len;
	struct rtattr *ifattr[IFLA_MAX+1];
	struct rtattr *ifinfo[IFLA_INFO_MAX+1];
	struct rtattr *ifgreo[EOIP_PARSE_MAX+1];
	const char *ifname;
	const char *kind;
	struct in_addr sip,dip;
	struct ifinfomsg *ifi;

	sip.s_addr=dip.s_addr=htonl(0);

	if (n->nlmsg_type != RTM_NEWLINK && n->nlmsg_type != RTM_DELLINK) {
		fprintf(stderr, "Not RTM_xxxLINK: %08x %08x %08x\n", n->nlmsg_len, n->nlmsg_type, n->nlmsg_flags);
		return 0;
	}
	len -= NLMSG_LENGTH(sizeof(*r));
	if (len < 0) {
		fprintf(stderr, "BUG: wrong nlmsg len %d\n", len);
		return -1;
	}

	ifi=(void *)r;

	parse_rtattr(ifattr, IFLA_MAX, IFLA_RTA(r), n->nlmsg_len - NLMSG_LENGTH(sizeof(*r)));
	if (ifattr[IFLA_IFNAME])
		ifname=rta_getattr_str(ifattr[IFLA_IFNAME]);
	else
		ifname="";
	if (ifattr[IFLA_LINKINFO])
		parse_rtattr_nested(ifinfo, IFLA_INFO_MAX, ifattr[IFLA_LINKINFO]);
	else
		memset(ifinfo,0,sizeof ifinfo);
	if (ifinfo[IFLA_INFO_KIND])
		kind=rta_getattr_str(ifinfo[IFLA_INFO_KIND]);
	else
		kind="";
	if (!strcmp(kind,"eoip") && ifinfo[IFLA_INFO_DATA]) {
		char ts[IFNAMSIZ],td[IFNAMSIZ],kbuf[40];
		uint8_t ttl=0,tos=0;
		int tunid=0;
		int link=0;

		parse_rtattr_nested(ifgreo, EOIP_PARSE_MAX, ifinfo[IFLA_INFO_DATA]);
		if (ifgreo[IFLA_GRE_LINK])
			link=rta_getattr_u32(ifgreo[IFLA_GRE_LINK]);
		if (ifgreo[IFLA_GRE_TOS])
			tos=rta_getattr_u8(ifgreo[IFLA_GRE_TOS]);
		if (ifgreo[IFLA_GRE_TTL])
			ttl=rta_getattr_u8(ifgreo[IFLA_GRE_TTL]);
		if (ifgreo[IFLA_GRE_LOCAL])
			sip.s_addr=rta_getattr_u32(ifgreo[IFLA_GRE_LOCAL]);
		if (ifgreo[IFLA_GRE_REMOTE])
			dip.s_addr=rta_getattr_u32(ifgreo[IFLA_GRE_REMOTE]);
		if (ifgreo[IFLA_GRE_IKEY])
			tunid=rta_getattr_u32(ifgreo[IFLA_GRE_IKEY]);
		ka_suffix(ifgreo,kbuf,sizeof kbuf);
		strcpy(ts,inet_ntoa(sip));
		strcpy(td,inet_ntoa(dip));
		printf("%d: %s@%d: link/%s %s remote %s tunnel-id %d ttl %d tos %d%s\n",ifi->ifi_index,ifname,link,kind,ts,td,tunid,ttl,tos,kbuf);
	} else if (!strcmp(kind,"eoipv6") && ifinfo[IFLA_INFO_DATA]) {
		char ts[INET6_ADDRSTRLEN],td[INET6_ADDRSTRLEN],kbuf[40];
		uint8_t ttl=0,tos=0;
		int tunid=0;
		int link=0;

		parse_rtattr_nested(ifgreo, EOIP_PARSE_MAX, ifinfo[IFLA_INFO_DATA]);
		strcpy(ts,"::");
		strcpy(td,"::");
		if (ifgreo[IFLA_GRE_LINK])
			link=rta_getattr_u32(ifgreo[IFLA_GRE_LINK]);
		if (ifgreo[IFLA_GRE_TOS])
			tos=rta_getattr_u8(ifgreo[IFLA_GRE_TOS]);
		if (ifgreo[IFLA_GRE_TTL])
			ttl=rta_getattr_u8(ifgreo[IFLA_GRE_TTL]);
		if (ifgreo[IFLA_GRE_LOCAL]&&RTA_PAYLOAD(ifgreo[IFLA_GRE_LOCAL])>=16)
			inet_ntop(AF_INET6,RTA_DATA(ifgreo[IFLA_GRE_LOCAL]),ts,sizeof ts);
		if (ifgreo[IFLA_GRE_REMOTE]&&RTA_PAYLOAD(ifgreo[IFLA_GRE_REMOTE])>=16)
			inet_ntop(AF_INET6,RTA_DATA(ifgreo[IFLA_GRE_REMOTE]),td,sizeof td);
		if (ifgreo[IFLA_GRE_IKEY])
			tunid=rta_getattr_u32(ifgreo[IFLA_GRE_IKEY]);
		ka_suffix(ifgreo,kbuf,sizeof kbuf);
		printf("%d: %s@%d: link/%s %s remote %s tunnel-id %d ttl %d tos %d%s\n",ifi->ifi_index,ifname,link,kind,ts,td,tunid,ttl,tos,kbuf);
	}

	return 0;
}

static int list(void) {
	struct rtnl_handle rth;

	if (rtnl_open(&rth,0)) {
		perror("Cannot open rtnetlink");
		return -1;
	}
	if (rtnl_wilddump_request(&rth, AF_UNSPEC, RTM_GETLINK) < 0) {
		perror("Cannot send dump request");
		rtnl_close(&rth);
		return -1;
	}

	if (rtnl_dump_filter(&rth, print_link, NULL) < 0) {
		fprintf(stderr, "Dump terminated\n");
		rtnl_close(&rth);
		return -1;
	}
	rtnl_close(&rth);
	return 0;
}

static int eoip_remove_index(unsigned int index) {
	struct {
		struct nlmsghdr msg;
		struct ifinfomsg ifi;
	} req;
	struct rtnl_handle rth = { .fd = -1 };
	int result;
	if (!index || index > 0x7fffffffU) return 1;
	memset(&req, 0, sizeof(req));
	req.msg.nlmsg_len = NLMSG_LENGTH(sizeof(req.ifi));
	req.msg.nlmsg_type = RTM_DELLINK;
	req.msg.nlmsg_flags = NLM_F_REQUEST;
	req.ifi.ifi_family = AF_UNSPEC;
	req.ifi.ifi_index = index;
	if (rtnl_open(&rth, 0) < 0) {
		rtnl_close(&rth);
		return 2;
	}
	result = rtnl_talk(&rth, &req.msg, 0, 0, NULL);
	rtnl_close(&rth);
	return result < 0 ? 2 : 0;
}
static int eoip_remove(const char *name) {
	unsigned int index;
	if (!name || !*name || strlen(name) >= IFNAMSIZ ||
	    strchr(name, '/') || strchr(name, ':') || strchr(name, ' ') ||
	    strchr(name, '\t') || strchr(name, '\n')) {
		fprintf(stderr, "invalid interface name\n");
		return 1;
	}
	index = if_nametoindex(name);
	if (!index) {
		fprintf(stderr, "unable to get interface %s index: %s\n", name, strerror(errno));
		return 3;
	}
	return eoip_remove_index(index);
}
static int eoip_remove_owned(unsigned slot,unsigned expected_index) {
	char name[16],owner[32];struct wr_eoip_observation observation;int result;
	if(slot>7 || !expected_index || expected_index>0x7fffffffU)return 1;
	snprintf(name,sizeof(name),"wr-eoip%u",slot);
	snprintf(owner,sizeof(owner),"wr-eoip:%u:v1",slot);
	result=WR_EOIP_QUERY_LINK(name,owner,&observation);
	if(result==1)return 0;
	if(result!=2 || !observation.owned || observation.ifindex!=(int)expected_index)return 3;
	result=eoip_remove_index(expected_index);if(result)return result;
	return WR_EOIP_QUERY_LINK(name,owner,&observation)==1?0:4;
}

static int eoip_add(int excl,char *name,uint32_t tunnelid,int af,void *sip,void *dip,uint32_t link,uint8_t ttl,uint8_t tos,int kaset,uint32_t kai,uint8_t kar,const char *owner) {
	struct {
		struct nlmsghdr msg;
		struct ifinfomsg ifi;
		uint8_t buf[1024];
	} req;
	struct rtnl_handle rth = { .fd = -1 };
	struct rtattr *lnfo;
	struct rtattr *data;
	int alen=af==AF_INET6?16:4;
	const char *kind=af==AF_INET6?"eoipv6":"eoip";

	memset(&req, 0, sizeof(req));
	req.msg.nlmsg_type = RTM_NEWLINK;
	req.msg.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg));
	req.msg.nlmsg_flags = NLM_F_REQUEST | NLM_F_CREATE | (excl ? NLM_F_EXCL : 0);
	req.ifi.ifi_family = AF_UNSPEC;

	// an empty IFLA_IFNAME fails kernel policy validation with ERANGE;
	// omit the attribute and the kernel will pick a free eoip%d name
	if (*name)
		addattr_l(&req.msg, sizeof(req), IFLA_IFNAME, name, strlen(name)+1);
	if (*owner)
		addattr_l(&req.msg, sizeof(req), IFLA_IFALIAS, owner, strlen(owner)+1);
	lnfo = NLMSG_TAIL(&req.msg);
	addattr_l(&req.msg, sizeof(req), IFLA_LINKINFO, NULL, 0);
	addattr_l(&req.msg, sizeof(req), IFLA_INFO_KIND, kind, strlen(kind)+1);
	data = NLMSG_TAIL(&req.msg);
	addattr_l(&req.msg, sizeof(req), IFLA_INFO_DATA, NULL, 0);

	addattr32(&req.msg, sizeof(req), IFLA_GRE_IKEY, tunnelid);
	addattr_l(&req.msg, sizeof(req), IFLA_GRE_LOCAL, sip, alen);
	addattr_l(&req.msg, sizeof(req), IFLA_GRE_REMOTE, dip, alen);
	addattr32(&req.msg, sizeof(req), IFLA_GRE_LINK, link);
	addattr8(&req.msg, sizeof(req), IFLA_GRE_TTL, ttl);
	addattr8(&req.msg, sizeof(req), IFLA_GRE_TOS, tos);
	// only when requested, so that set does not clobber keepalive
	if (kaset) {
		addattr32(&req.msg, sizeof(req), IFLA_EOIP_KA_INTERVAL, kai);
		addattr8(&req.msg, sizeof(req), IFLA_EOIP_KA_RETRIES, kar);
	}

	data->rta_len = (void *)NLMSG_TAIL(&req.msg) - (void *)data;
	lnfo->rta_len = (void *)NLMSG_TAIL(&req.msg) - (void *)lnfo;


	if (rtnl_open(&rth, 0)) {
		fprintf(stderr, "cannot open netlink\n");
		return -1;
	}

	if (rtnl_talk(&rth, &req.msg, 0, 0, NULL) < 0) {
		fprintf(stderr, "failed to talk to netlink!\n");
		rtnl_close(&rth);
		return -1;
	}

	rtnl_close(&rth);
	return 0;
}

// parse an IPv4 or IPv6 address, recording the family
static int parse_addr(const char *s,int *af,void *buf) {
	if (inet_pton(AF_INET,s,buf)==1) {
		*af=AF_INET;
		return 0;
	}
	if (inet_pton(AF_INET6,s,buf)==1) {
		*af=AF_INET6;
		return 0;
	}
	return -1;
}

/* strict numeric argument parser; returns 0 and stores the value only
 * for a fully numeric string within [0, max]
 */
static int parse_num(const char *s,unsigned long max,unsigned long *val) {
	char *end;
	unsigned long v;

	if (!s||!*s)
		return -1;
	errno=0;
	v=strtoul(s,&end,0);
	if (errno||*end||v>max)
		return -1;
	*val=v;
	return 0;
}

typedef enum {
	E_AMBIGUOUS = -1,
	E_NONE = 0,
	C_LIST,
	C_ADD,
	C_SET,
	C_REMOVE,
	C_REMOVE_OWNED,
	C_VER,
	C_HELP,
	P_LOCAL,
	P_REMOTE,
	P_TUNNELID,
	P_TTL,
	P_TOS,
	P_LINK,
	P_NAME,
	P_KEEPALIVE,
	P_OWNER,
} e_cmd;

typedef struct {
	char *cmd;
	e_cmd cid;
} s_cmd;

static s_cmd cmds[] = {
	{ .cmd = "list", .cid = C_LIST, },
	{ .cmd = "show", .cid = C_LIST, },
	{ .cmd = "add", .cid = C_ADD, },
	{ .cmd = "new", .cid = C_ADD, },
	{ .cmd = "set", .cid = C_SET, },
	{ .cmd = "change", .cid = C_SET, },
	{ .cmd = "remove", .cid = C_REMOVE, },
	{ .cmd = "owned-remove", .cid = C_REMOVE_OWNED, },
	{ .cmd = "version", .cid = C_VER, },
	{ .cmd = "--version", .cid = C_VER, },
	{ .cmd = "-v", .cid = C_VER, },
	{ .cmd = "help", .cid = C_HELP, },
	{ .cmd = "--help", .cid = C_HELP, },
	{ .cmd = "-h", .cid = C_HELP, },
	{ .cmd = NULL, .cid = 0, },
};

static s_cmd prms[] = {
	{ .cmd = "local", .cid = P_LOCAL, },
	{ .cmd = "remote", .cid = P_REMOTE, },
	{ .cmd = "tunnel-id", .cid = P_TUNNELID, },
	{ .cmd = "tid", .cid = P_TUNNELID, },
	{ .cmd = "ttl", .cid = P_TTL, },
	{ .cmd = "tos", .cid = P_TOS, },
	{ .cmd = "link", .cid = P_LINK, },
	{ .cmd = "name", .cid = P_NAME, },
	{ .cmd = "keepalive", .cid = P_KEEPALIVE, },
	{ .cmd = "owner", .cid = P_OWNER, },
	{ .cmd = NULL, .cid = 0, },
};

static e_cmd find_cmd(s_cmd *l, char *pcmd) {
	int cnt=0;
	int len=0;
	e_cmd match=E_NONE;

	while (l && pcmd && l->cmd) {
		char *ha = l->cmd;
		char *ne = pcmd;
		int clen = 0;

		while (*ha && *ne && *ha == *ne)
			ha++, ne++, clen++;

		if (!*ne) {
			if (clen && clen > len) {
				cnt = 0;
				len = clen;
				match = l->cid;
			}
			if (clen && clen == len)
				cnt++;
		}
		l++;
	}
	if (cnt == 1)
		return match;
	return cnt ? E_AMBIGUOUS : E_NONE;
}

static void version(void) {
	printf("eoip version %s\n",EOIP_VERSION);
}

static void usage(char *me) {
	printf("usage:\n"
		"\t%s add [name <name>] tunnel-id <id> [local <ip>] remote <ip> [ttl <ttl>] [tos <tos>] [link <ifindex|ifname>] [keepalive none|<secs>[,<retries>]]\n"
		"\t%s set  name <name>  tunnel-id <id> [local <ip>] remote <ip> [ttl <ttl>] [tos <tos>] [link <ifindex|ifname>] [keepalive none|<secs>[,<retries>]]\n"
		"\t%s remove name <name>\n"
		"\t%s list\n"
		"\t%s version\n"
		"notes:\n"
		"\tIPv6 local/remote addresses select the eoipv6 tunnel kind (tunnel-id 0..4095)\n"
		"\tkeepalive is off by default; retries defaults to 10 (the RouterOS default is 10,10); retries 0 means send-only\n"
		"\towner wr-eoip:<0..7>:v1 is permitted only with add name wr-eoip<slot> over IPv4\n"
		"\towned-remove <slot 0..7> <expected-ifindex> checks type/alias/index before deletion\n"
		,me,me,me,me,me);
}

int main(int argc,char **argv) {
	if (argc >= 1) {
		e_cmd c = (argc == 1) ? C_LIST : find_cmd(cmds, argv[1]);
		int excl = 1;

		switch (c) {
			dafeutl:
			default:
				usage(argv[0]);
				return 1;
			case C_HELP:
				usage(argv[0]);
				return 0;
			case C_VER:
				version();
				return 0;
			case C_LIST:
				if (argc > 2)
					goto dafeutl;
				return list()?1:0;
			case C_REMOVE:
				if (argc != 4 || find_cmd(prms, argv[2]) != P_NAME) {
					usage(argv[0]);
					return 1;
				}
				return eoip_remove(argv[3]);
			case C_REMOVE_OWNED: {
				unsigned long slot,index;
				if(argc!=4 || parse_num(argv[2],7,&slot) ||
				   parse_num(argv[3],0x7fffffff,&index) || !index)return 1;
				return eoip_remove_owned((unsigned)slot,(unsigned)index);
			}
			case C_SET:
				excl = 0;
				// fall through
			case C_ADD: {
				char ifname[IFNAMSIZ + 1] = "";
				char owner[13] = "";
				unsigned char sip[16]={0},dip[16]={0};
				int saf=0,daf=0,af;
				uint32_t tid = ~0;
				uint8_t ttl=0, tos=0;
				uint32_t link = 0;
				uint32_t kai=0;
				uint8_t kar=0;
				int kaset=0;
				int i=2;

				while (i < argc) {
					e_cmd p = find_cmd(prms, argv[i]);
					int noarg=!((i + 1) < argc);
					unsigned long num;

					switch (p) {
						default:
							break;
						case E_NONE:
							printf("unknown option: %s\n", argv[i]);
							return 1;
						case E_AMBIGUOUS:
							printf("option is ambiguous: %s\n", argv[i]);
							return 1;
					}

					if (noarg) {
						printf("option: %s requires an argument\n", argv[i]);
						return 1;
					}

					switch (p) {
						default:
							printf("BUG!\n");
							return 1;
						case P_NAME:
							if (strlen(argv[i+1])>=IFNAMSIZ) {
								printf("interface name too long: %s\n",argv[i+1]);
								return 1;
							}
							strcpy(ifname,argv[i+1]);
							break;
						case P_OWNER:
							if (*owner || strlen(argv[i+1])!=12 ||
							    strncmp(argv[i+1],"wr-eoip:",8) ||
							    argv[i+1][8]<'0' || argv[i+1][8]>'7' ||
							    strcmp(argv[i+1]+9,":v1")) {
								fprintf(stderr,"invalid managed owner\n");return 1;
							}
							strcpy(owner,argv[i+1]);break;
						case P_TTL:
							if (parse_num(argv[i+1],0xff,&num)) {
								printf("invalid ttl value: %s\n",argv[i+1]);
								return 1;
							}
							ttl=num;
							break;
						case P_TOS:
							if (parse_num(argv[i+1],0xff,&num)) {
								printf("invalid tos value: %s\n",argv[i+1]);
								return 1;
							}
							tos=num;
							break;
						case P_LINK:
							// convert ifname to ifindex, also support numeric arg
							link=if_nametoindex(argv[i+1]);
							if (!link) {
								if (parse_num(argv[i+1],0x7fffffff,&num)||!num) {
									printf("invalid interface name/index: %s\n",argv[i+1]);
									return 1;
								}
								link=num;
							}
							break;
						case P_TUNNELID:
							if (parse_num(argv[i+1],0xffff,&num)) {
								printf("invalid tunnel-id value: %s\n",argv[i+1]);
								return 1;
							}
							tid=num;
							break;
						case P_LOCAL:
							if (parse_addr(argv[i+1],&saf,sip)) {
								printf("invalid ip address: %s\n",argv[i+1]);
								return 1;
							}
							break;
						case P_REMOTE:
							if (parse_addr(argv[i+1],&daf,dip)) {
								printf("invalid ip address: %s\n",argv[i+1]);
								return 1;
							}
							break;
						case P_KEEPALIVE: {
							char *c=strchr(argv[i+1],',');

							kaset=1;
							if (!strcmp(argv[i+1],"none")) {
								kai=0;
								kar=0;
								break;
							}
							if (c)
								*c=0;
							if (parse_num(argv[i+1],EOIP_KA_MAX_INTERVAL,&num)) {
								printf("invalid keepalive interval: %s\n",argv[i+1]);
								return 1;
							}
							kai=num;
							if (c) {
								if (parse_num(c+1,0xff,&num)) {
									printf("invalid keepalive retries: %s\n",c+1);
									return 1;
								}
								kar=num;
							} else
								kar=EOIP_KA_DEF_RETRIES;
							if (!kai)
								kar=0;
							break;
						}
					}
					i += 2;
				}
				if (tid==~0U) {
					printf("tunnel-id is mandatory parameter\n");
					return 1;
				}
				if (!excl&&!*ifname) {
					printf("name is mandatory for set/change\n");
					return 1;
				}
				if (saf&&daf&&saf!=daf) {
					printf("local/remote address family mismatch\n");
					return 1;
				}
				// IPv6 addresses select the eoipv6 tunnel kind
				af=saf?saf:daf?daf:AF_INET;
				if (*owner) {
					char expected[16];
					snprintf(expected,sizeof(expected),"wr-eoip%c",owner[8]);
					if (!excl || af!=AF_INET || strcmp(ifname,expected)) {
						fprintf(stderr,"owner requires exclusive matching IPv4 interface creation\n");return 1;
					}
				}
				if (af==AF_INET6&&tid>EOIP6_TID_MAX) {
					printf("tunnel-id must be 0..%d for eoipv6\n",EOIP6_TID_MAX);
					return 1;
				}
				// tunnel id is in host byte order, addresses are in net byte order
				return eoip_add(excl,ifname,tid,af,sip,dip,link,ttl,tos,kaset,kai,kar,owner)?1:0;
			}
		}
	}
	return 0;
}
