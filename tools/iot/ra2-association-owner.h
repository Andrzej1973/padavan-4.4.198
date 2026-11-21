/* Adapter-local ra2 arbitration. Every call requires the same caller-owned
 * lock. No spinning, allocation, callbacks, firmware or implicit retry.
 * Tickets are private linear stack objects: never copy or retain after leave.
 * This header alone does not bind the native station mutation paths. */
#ifndef WR_IOT_RA2_ASSOCIATION_OWNER_H
#define WR_IOT_RA2_ASSOCIATION_OWNER_H
struct wr_ra2_assoc_owner {
 unsigned int associations,key_active,poisoned;
 unsigned long serial,key_serial;
};
struct wr_ra2_assoc_ticket {
 struct wr_ra2_assoc_owner *owner;
 unsigned long serial;
 unsigned int active,key;
};
static inline int wr_ra2_assoc_enter(struct wr_ra2_assoc_owner *owner,
 struct wr_ra2_assoc_ticket *ticket,int key)
{
 if(!owner||!ticket||ticket->active||owner->poisoned||owner->key_active||
    (key&&owner->associations))return 0;
 if(owner->serial==~0UL||(!key&&owner->associations==~0U)){
  owner->poisoned=1;return 0;
 }
 ticket->owner=owner;ticket->serial=++owner->serial;
 ticket->key=key!=0;ticket->active=1;
 if(key){owner->key_active=1;owner->key_serial=ticket->serial;}
 else ++owner->associations;
 return 1;
}
static inline int wr_ra2_assoc_leave(struct wr_ra2_assoc_owner *owner,
 struct wr_ra2_assoc_ticket *ticket)
{
 if(!owner||!ticket||!ticket->active||ticket->owner!=owner||
    !ticket->serial||ticket->serial>owner->serial)return 0;
 if(ticket->key){
  if(owner->key_active!=1||owner->key_serial!=ticket->serial){
   owner->poisoned=1;return 0;
  }
  owner->key_active=0;owner->key_serial=0;
 }else{
  if(!owner->associations||owner->key_active){owner->poisoned=1;return 0;}
  --owner->associations;
 }
 ticket->active=0;ticket->owner=0;ticket->serial=0;ticket->key=0;
 return !owner->poisoned;
}
#endif
