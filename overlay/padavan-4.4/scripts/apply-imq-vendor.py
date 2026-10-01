#!/usr/bin/env python3
"""Adapt IMQ 4.9 patch rejects to vipshmily Padavan Linux 4.4.198."""
from pathlib import Path
root = Path("padavan-4.4/trunk/linux-4.4.x")
def replace_once(relative, old, new):
    path = root / relative
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{relative}: expected one anchor, found {count}")
    path.write_text(text.replace(old, new, 1))
replace_once("include/linux/skbuff.h", """\t__u8\t\t\tremcsum_offload:1;
\t__u8\t\t\tgro_skip:1;
\t/* 2 or 4 bit hole */
""", """\t__u8\t\t\tremcsum_offload:1;
\t__u8\t\t\tgro_skip:1;
#if defined(CONFIG_IMQ) || defined(CONFIG_IMQ_MODULE)
\t__u8\t\t\timq_flags:IMQ_F_BITS;
#endif
\t/* 2 or 4 bit hole */
""")
replace_once("net/core/dev.c", """#include <linux/netfilter_ingress.h>

#include "net-sysfs.h"
""", """#include <linux/netfilter_ingress.h>
#if defined(CONFIG_IMQ) || defined(CONFIG_IMQ_MODULE)
#include <linux/imq.h>
#endif

#include "net-sysfs.h"
""")
replace_once("net/core/dev.c", """#ifdef CONFIG_SHORTCUT_FE
\t}
#endif
\tif (!list_empty(&ptype_all) || !list_empty(&dev->ptype_all))
\t\tdev_queue_xmit_nit(skb, dev);
""", """#ifdef CONFIG_SHORTCUT_FE
\t}
#endif
#if defined(CONFIG_IMQ) || defined(CONFIG_IMQ_MODULE)
\tif ((!list_empty(&ptype_all) || !list_empty(&dev->ptype_all)) &&
\t    !(skb->imq_flags & IMQ_F_ENQUEUE))
#else
\tif (!list_empty(&ptype_all) || !list_empty(&dev->ptype_all))
#endif
\t\tdev_queue_xmit_nit(skb, dev);
""")
replace_once("net/netfilter/core.c", """} else if ((verdict & NF_VERDICT_MASK) == NF_QUEUE) {
\t\tint err = nf_queue(skb, elem, state,
\t\t\t\t   verdict >> NF_VERDICT_QBITS);
\t\tif (err < 0) {
""", """} else if ((verdict & NF_VERDICT_MASK) == NF_QUEUE ||
\t\t   (verdict & NF_VERDICT_MASK) == NF_IMQ_QUEUE) {
\t\tint err = nf_queue(skb, elem, state, verdict);
\t\tif (err == -ECANCELED)
\t\t\tgoto next_hook;
\t\tif (err < 0) {
""")
replace_once("net/netfilter/nf_queue.c", """\t     struct nf_hook_state *state,
\t     unsigned int queuenum)
{
\tint status = -ENOENT;
\tstruct nf_queue_entry *entry = NULL;
\tconst struct nf_afinfo *afinfo;
\tconst struct nf_queue_handler *qh;
\tstruct net *net = state->net;

\t/* QUEUE == DROP if no one is waiting, to be safe. */
\tqh = rcu_dereference(net->nf.queue_handler);
""", """\t     struct nf_hook_state *state,
\t     unsigned int verdict)
{
\tint status = -ENOENT;
\tstruct nf_queue_entry *entry = NULL;
\tconst struct nf_afinfo *afinfo;
\tconst struct nf_queue_handler *qh;
\tstruct net *net = state->net;
\tunsigned int queuetype = verdict & NF_VERDICT_MASK;
\tunsigned int queuenum = verdict >> NF_VERDICT_QBITS;

\t/* QUEUE == DROP if no one is waiting, to be safe. */
\tif (queuetype == NF_IMQ_QUEUE) {
#if defined(CONFIG_IMQ) || defined(CONFIG_IMQ_MODULE)
\t\tqh = rcu_dereference(queue_imq_handler);
#else
\t\treturn -EINVAL;
#endif
\t} else {
\t\tqh = rcu_dereference(net->nf.queue_handler);
\t}
""")
replace_once("net/netfilter/nf_queue.c", """\tcase NF_QUEUE:
\t\terr = nf_queue(skb, elem, &entry->state,
\t\t\t       verdict >> NF_VERDICT_QBITS);
\t\tif (err < 0) {
""", """\tcase NF_QUEUE:
\tcase NF_IMQ_QUEUE:
\t\terr = nf_queue(skb, elem, &entry->state, verdict);
#if defined(CONFIG_IMQ) || defined(CONFIG_IMQ_MODULE)
\t\tif (err == -ECANCELED && skb->imq_flags == 0)
\t\t\tgoto next_hook;
#endif
\t\tif (err < 0) {
""")
