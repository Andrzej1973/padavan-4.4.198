"""Isolated candidate composition: both GTK writers share the ra2 arbiter.

Installed together with native mutation, insertion and periodic peer scopes.
"""


def one(text, old, new):
    if text.count(old)!=1:
        raise ValueError('key arbitration anchor changed: '+old[:90])
    return text.replace(old,new,1)


def request_header(text):
    text=one(text,'#include "assoc-generation-kernel.h"',
             '#include "assoc-generation-kernel.h"\n#include "ra2-association-owner.h"')
    text=one(text,' unsigned int active,wcid,generation;',
             ' unsigned int active,wcid,generation;\n struct wr_ra2_assoc_ticket key_ticket;')
    text=one(text,'wr_iot_ra2_gtk_control_leave(RTMP_ADAPTER *ad,int failed)',
             'wr_iot_ra2_gtk_control_leave(RTMP_ADAPTER *ad,int failed,struct wr_ra2_assoc_ticket *key_ticket)')
    text=one(text,' if(ad->wr_iot_ra2_key_active!=1)failed=1;',
             ' if(!wr_ra2_assoc_leave(&ad->wr_ra2_assoc_owner,key_ticket))failed=1;\n'
             ' if(ad->wr_iot_ra2_key_active!=1)failed=1;')
    text=one(text,'  if(admitted)ad->wr_iot_ra2_key_active=1;',
             '  if(admitted&&!wr_ra2_assoc_enter(&ad->wr_ra2_assoc_owner,&scope->key_ticket,1)){\n'
             '   --ad->wr_iot_control_users;admitted=0;\n'
             '   if(ad->wr_ra2_assoc_owner.poisoned)ad->wr_iot_control_poisoned=1;\n'
             '  }\n  if(admitted)ad->wr_iot_ra2_key_active=1;')
    if text.count('wr_iot_ra2_gtk_control_leave(ad,0);')!=2:
        raise ValueError('request admission rollback sites changed')
    text=text.replace('wr_iot_ra2_gtk_control_leave(ad,0);',
                      'wr_iot_ra2_gtk_control_leave(ad,0,&scope->key_ticket);')
    return one(text,'wr_iot_ra2_gtk_control_leave(ad,failed);',
               'wr_iot_ra2_gtk_control_leave(ad,failed,&scope->key_ticket);')


def periodic(text):
    text=one(text,'#include "ra2-rekey-admission.h"',
             '#include "ra2-rekey-admission.h"\n#include "ra2-association-owner.h"')
    text=one(text,'  ULONG flags=0;int admitted=0;',
             '  ULONG flags=0;int admitted=0;\n  struct wr_ra2_assoc_ticket key_ticket={0};')
    text=one(text,'  if(admitted)ad->wr_iot_ra2_key_active=1;',
             '  if(admitted&&!wr_ra2_assoc_enter(&ad->wr_ra2_assoc_owner,&key_ticket,1)){\n'
             '   --ad->wr_iot_control_users;admitted=0;\n'
             '   if(ad->wr_ra2_assoc_owner.poisoned)ad->wr_iot_control_poisoned=1;\n'
             '  }\n  if(admitted)ad->wr_iot_ra2_key_active=1;')
    return one(text,'   if(ad->wr_iot_ra2_key_active==1)ad->wr_iot_ra2_key_active=0;',
               '   if(!wr_ra2_assoc_leave(&ad->wr_ra2_assoc_owner,&key_ticket))\n'
               '    ad->wr_iot_control_poisoned=1;\n'
               '   if(ad->wr_iot_ra2_key_active==1)ad->wr_iot_ra2_key_active=0;')


def periodic_peer_scope(text):
    """Add retained peers around the already arbitrated periodic native body."""
    text=one(text,'#include "ra2-association-owner.h"',
             '#include "ra2-association-owner.h"\n#include "ra2-rekey-peer-scope.h"')
    text=one(text,'  struct wr_ra2_assoc_ticket key_ticket={0};',
             '  struct wr_ra2_assoc_ticket key_ticket={0};\n'
             '  struct wr_ra2_rekey_peer_scope peers;int peer_ok=0;')
    text=one(text,'   wr_iot_grekey_periodic_raw(s1,context,s2,timer);',
             '   if(wr_ra2_rekey_peers_enter(ad,&peers)){\n'
             '    wr_iot_grekey_periodic_raw(s1,context,s2,timer);\n'
             '    peer_ok=wr_ra2_rekey_peers_leave(ad,&peers);\n'
             '   }else peer_ok=1; /* No native mutation on admission refusal. */')
    return one(text,'   if(!wr_ra2_assoc_leave(&ad->wr_ra2_assoc_owner,&key_ticket))',
               '   if(!peer_ok)ad->wr_iot_control_poisoned=1;\n'
               '   if(!wr_ra2_assoc_leave(&ad->wr_ra2_assoc_owner,&key_ticket))')
