type
  PendingState = enum
    psFree, psLive, psRetired, psClaimed
  Ticket = object
    generation: uint32
    slot: int
    bss: uint32
    mac: array[6, uint8]
  Slot = object
    nextGeneration: uint32
    generation: uint32
    references: uint32
    bss: uint32
    mac: array[6, uint8]
    state: PendingState
    poisoned: bool
  Ledger = array[3, Slot]

proc current(ledger: Ledger, ticket: Ticket): bool =
  if ticket.generation == 0 or ticket.slot < 0 or ticket.slot >= ledger.len:
    return false
  let slot = ledger[ticket.slot]
  slot.state == psLive and slot.generation == ticket.generation and
    slot.references > 0 and slot.bss == ticket.bss and slot.mac == ticket.mac

proc reserve(ledger: var Ledger, bss: uint32, mac: array[6, uint8],
             ticket: var Ticket): bool =
  for i in 0 ..< ledger.len:
    if ledger[i].state == psClaimed and ledger[i].bss == bss and
       ledger[i].mac == mac:
      return false
    if ledger[i].state == psLive and ledger[i].bss == bss and
       ledger[i].mac == mac:
      if ledger[i].references == high(uint32):
        return false
      inc ledger[i].references
      ticket = Ticket(generation: ledger[i].generation, slot: i, bss: bss, mac: mac)
      return true
  for i in 0 ..< ledger.len:
    if ledger[i].state != psFree or ledger[i].references != 0 or
       ledger[i].poisoned:
      continue
    if ledger[i].nextGeneration == high(uint32):
      ledger[i].poisoned = true
      continue
    inc ledger[i].nextGeneration
    if ledger[i].nextGeneration == 0:
      ledger[i].poisoned = true
      continue
    ledger[i].generation = ledger[i].nextGeneration
    ledger[i].references = 1
    ledger[i].bss = bss
    ledger[i].mac = mac
    ledger[i].state = psLive
    ticket = Ticket(generation: ledger[i].generation, slot: i, bss: bss, mac: mac)
    return true
  false

proc claim(ledger: var Ledger, ticket: Ticket): bool =
  if not current(ledger, ticket):
    return false
  ledger[ticket.slot].state = psClaimed
  true

proc unclaim(ledger: var Ledger, ticket: Ticket): bool =
  if ticket.generation == 0 or ticket.slot < 0 or ticket.slot >= ledger.len:
    return false
  let slot = ledger[ticket.slot]
  if slot.state != psClaimed or slot.generation != ticket.generation or
     slot.references == 0 or slot.bss != ticket.bss or slot.mac != ticket.mac:
    return false
  ledger[ticket.slot].state = psLive
  true

proc retire(ledger: var Ledger, bss: uint32, mac: array[6, uint8]): int =
  for i in 0 ..< ledger.len:
    if ledger[i].state in {psLive, psClaimed} and ledger[i].bss == bss and
       ledger[i].mac == mac:
      ledger[i].state = psRetired
      inc result

proc release(ledger: var Ledger, ticket: Ticket): bool =
  if ticket.generation == 0 or ticket.slot < 0 or ticket.slot >= ledger.len:
    return false
  var slot = addr ledger[ticket.slot]
  if slot.generation != ticket.generation or slot.bss != ticket.bss or
     slot.mac != ticket.mac or slot.references == 0:
    return false
  dec slot.references
  if slot.references == 0:
    slot.state = psFree
    slot.generation = 0
    slot.bss = 0
    slot.mac = default(array[6, uint8])
  true

var ledger: Ledger
let macA: array[6, uint8] = [0'u8, 1, 2, 3, 4, 5]
let macB: array[6, uint8] = [0'u8, 1, 2, 3, 4, 6]
var first, shared, otherBss, third, reused, spare: Ticket
doAssert reserve(ledger, 1, macA, first)
doAssert current(ledger, first)
doAssert reserve(ledger, 1, macA, shared)
doAssert shared.slot == first.slot and shared.generation == first.generation
doAssert ledger[first.slot].references == 2
doAssert reserve(ledger, 2, macA, otherBss)
doAssert otherBss.slot != first.slot and current(ledger, otherBss)
doAssert reserve(ledger, 3, macB, third)
doAssert claim(ledger, first)
doAssert not current(ledger, first)
doAssert not reserve(ledger, 1, macA, spare)
doAssert not claim(ledger, shared)
doAssert unclaim(ledger, first) and current(ledger, shared)
doAssert claim(ledger, first)
doAssert retire(ledger, 1, macA) == 1
doAssert not current(ledger, first) and not unclaim(ledger, first)
doAssert current(ledger, otherBss)
doAssert not reserve(ledger, 1, macB, spare)
doAssert release(ledger, first)
doAssert not reserve(ledger, 1, macB, spare)
doAssert release(ledger, shared)
doAssert reserve(ledger, 1, macB, reused)
doAssert reused.slot == first.slot and reused.generation != first.generation
doAssert not current(ledger, first) and not release(ledger, first)
doAssert release(ledger, reused) and release(ledger, otherBss) and
  release(ledger, third)

ledger[0].nextGeneration = high(uint32)
doAssert reserve(ledger, 1, macA, spare)
doAssert ledger[0].poisoned and spare.slot != 0
doAssert release(ledger, spare)
echo "PASS | FT pending BSS+MAC ledger | single-use claim, unclaim, reference retirement, exact context, stale-token refusal, safe slot reuse, overflow poison"

# Linear queue ownership: success moves one existing reference. Refusal must
# leave the producer token intact, and take must not overwrite a live owner.
proc moveTicket(source: var Ticket, destination: var Ticket): bool =
  if source.generation == 0 or destination.generation != 0:
    return false
  destination = source
  source = default(Ticket)
  true

# Snapshot is read-only: the queue remains the sole reference owner.
proc snapshotTicket(source: Ticket, destination: var Ticket): bool =
  if source.generation == 0 or destination.generation != 0:
    return false
  destination = source
  true

var producer, queued, consumer: Ticket
doAssert reserve(ledger, 2, macB, producer)
let original = producer
doAssert moveTicket(producer, queued)
doAssert producer.generation == 0 and queued == original
doAssert ledger[queued.slot].references == 1
var queueSnapshot: Ticket
let refsBeforeSnapshot = ledger[queued.slot].references
doAssert snapshotTicket(queued, queueSnapshot) and queueSnapshot == original
doAssert queued == original and ledger[queued.slot].references == refsBeforeSnapshot
var occupiedSnapshot = original
doAssert not snapshotTicket(queued, occupiedSnapshot)
queueSnapshot = default(Ticket)
doAssert not moveTicket(producer, queued)
doAssert reserve(ledger, 2, macB, producer)
doAssert not moveTicket(producer, queued)
doAssert producer == original and ledger[queued.slot].references == 2
doAssert moveTicket(queued, consumer) and queued.generation == 0
doAssert not moveTicket(producer, consumer)
doAssert retire(ledger, 2, macB) == 1
doAssert not current(ledger, consumer)
doAssert release(ledger, consumer)
consumer = default(Ticket)
doAssert release(ledger, producer)
producer = default(Ticket)
doAssert not moveTicket(queued, consumer)
echo "PASS | FT pending queue ownership | one-reference move, read-only identity snapshot, refusal retention, occupied-owner refusal, stale drop release"

type
  QueueModel = object
    closed: bool
    count: int
    slots: array[3, Ticket]

proc queueMove(queue: var QueueModel, ticket: var Ticket, slot: int): bool =
  if queue.closed or slot < 0 or slot >= queue.slots.len or
     queue.count >= queue.slots.len or queue.slots[slot].generation != 0:
    return false
  if not moveTicket(ticket, queue.slots[slot]):
    return false
  inc queue.count
  true

proc queueDrain(queue: var QueueModel, ledger: var Ledger) =
  queue.closed = true
  for i in 0 ..< queue.slots.len:
    if queue.slots[i].generation != 0:
      doAssert release(ledger, queue.slots[i])
      queue.slots[i] = default(Ticket)
  queue.count = 0

var pendingQueue: QueueModel
var haltTicket, restartTicket: Ticket
doAssert reserve(ledger, 3, macA, haltTicket)
doAssert reserve(ledger, 3, macB, restartTicket)
doAssert queueMove(pendingQueue, haltTicket, 0) and haltTicket.generation == 0
doAssert queueMove(pendingQueue, restartTicket, 2) and restartTicket.generation == 0
pendingQueue.closed = true
doAssert reserve(ledger, 3, macA, haltTicket)
doAssert not queueMove(pendingQueue, haltTicket, 1)
doAssert current(ledger, haltTicket)
doAssert release(ledger, haltTicket)
queueDrain(pendingQueue, ledger)
doAssert pendingQueue.count == 0 and pendingQueue.closed
doAssert ledger[0].references == 0 and ledger[1].references == 0
# Restart drain closes admission, releases queued refs, then reopens the ring.
pendingQueue.closed = false
doAssert reserve(ledger, 3, macA, haltTicket)
doAssert queueMove(pendingQueue, haltTicket, 1)
queueDrain(pendingQueue, ledger)
pendingQueue.closed = false
doAssert not pendingQueue.closed and pendingQueue.count == 0
echo "PASS | FT pending queue lifecycle | close before drain, reject late producer, release queued refs, restart reopen"
