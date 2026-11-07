/* Candidate software receipt only. All operations use IRQ-safe CmdQLock;
 * joining itself runs outside that lock and RTNL. Adapter lifetime is external.
 * Initialize once before publication; never reset for reopen/retry.
 * Binding requires CmdQLock to have adapter lifetime, including never-open
 * and probe-unwind states. Vendor ring allocation currently reinitializes it;
 * do not call these helpers from early PCI remove until that is reconciled. */
#ifndef WR_IOT_TERMINAL_COMMAND_OWNER_H
#define WR_IOT_TERMINAL_COMMAND_OWNER_H
struct wr_iot_terminal_command_owner {
 unsigned long generation, attempt;
 unsigned int closed, joining, joined, attaching, create_failed;
};
static inline void wr_iot_terminal_command_init(
 struct wr_iot_terminal_command_owner *s, unsigned long generation)
{
 s->generation=generation;s->attempt=0;
 s->closed=0;s->joining=0;s->joined=0;s->attaching=0;s->create_failed=0;
}
static inline int wr_iot_terminal_command_enqueue_allowed(
 const struct wr_iot_terminal_command_owner *s)
{ return s && s->generation && !s->closed; }
/* Caller must also set CmdQState STOPPED in this same critical section. */
static inline int wr_iot_terminal_command_close(
 struct wr_iot_terminal_command_owner *s, unsigned long generation)
{
 if(!s || !generation || s->generation!=generation)return 0;
 s->closed=1;return 1;
}
/* A missing handle never manufactures an execution-completion receipt. */
static inline unsigned long wr_iot_terminal_command_join_begin(
 struct wr_iot_terminal_command_owner *s, unsigned long generation,
 int handle_present)
{
 if(!s || !generation || s->generation!=generation || !s->closed ||
    s->joining || s->attaching || s->joined || !handle_present || s->attempt==~0UL)return 0;
 s->joining=1;return ++s->attempt;
}
/* success must mean the actual synchronous task join returned successfully. */
static inline int wr_iot_terminal_command_join_finish(
 struct wr_iot_terminal_command_owner *s, unsigned long generation,
 unsigned long attempt, int success)
{
 if(!s || !generation || s->generation!=generation ||
    !attempt || s->attempt!=attempt || !s->joining || s->joined)return 0;
 s->joining=0;if(success)s->joined=1;return 1;
}
/* Normal close reserves the same execution owner as terminal join. */
static inline unsigned long wr_iot_command_normal_join_begin(
 struct wr_iot_terminal_command_owner *s, unsigned long generation,
 int handle_present)
{
 if(!s || !generation || s->generation!=generation || s->joining ||
    s->attaching || s->joined || !handle_present || s->attempt==~0UL)return 0;
 s->joining=1;return ++s->attempt;
}
/* First creation is reserved separately from reopen; no prior join receipt
 * exists. A failed creation does not itself manufacture worker quiescence. */
static inline unsigned long wr_iot_command_first_attach_begin(
 struct wr_iot_terminal_command_owner *s, unsigned long generation)
{
 if(!s || !generation || s->generation!=generation || s->closed ||
    s->attempt || s->joining || s->attaching || s->joined)return 0;
 s->attaching=1;return ++s->attempt;
}
/* Reopen must explicitly invalidate the old join receipt before OS attach.
 * Serialize with terminal close using the same adapter-lifetime CmdQLock. */
static inline unsigned long wr_iot_command_attach_begin(
 struct wr_iot_terminal_command_owner *s, unsigned long generation)
{
 if(!s || !generation || s->generation!=generation || s->closed ||
    s->joining || s->attaching || (!s->joined && !s->create_failed) || s->attempt==~0UL)return 0;
 s->joined=0;s->create_failed=0;s->attaching=1;return ++s->attempt;
}
static inline int wr_iot_command_attach_finish(
 struct wr_iot_terminal_command_owner *s, unsigned long generation,
 unsigned long attempt)
{
 if(!s || !generation || s->generation!=generation || !s->attaching ||
    !attempt || s->attempt!=attempt)return 0;
 s->attaching=0;return 1;
}
/* Explicit no-task proof from the exact failed creation, never handle absence. */
static inline int wr_iot_command_attach_failed_absent(
 struct wr_iot_terminal_command_owner *s, unsigned long generation,
 unsigned long attempt, int os_proved_no_task)
{
 if(!s || !generation || s->generation!=generation || !s->attaching ||
    !attempt || s->attempt!=attempt || os_proved_no_task!=1)return 0;
 s->attaching=0;s->create_failed=1;return 1;
}
/* Later CLOSE can reuse this fact without killing the task a second time.
 * This says nothing about timer callbacks, IRQs, DMA or adapter release. */
static inline int wr_iot_terminal_command_joined(
 const struct wr_iot_terminal_command_owner *s, unsigned long generation)
{
 return s && generation && s->generation==generation && s->closed &&
        !s->joining && s->joined;
}
/* attempt==0 is a positive never-started receipt only because every initial
 * attach reserves/increments it BEFORE OS task initialization/creation. This
 * A failed creation additionally needs its exact OS no-task proof. This
 * concerns worker execution, not queued buffers or timer producer lifetime. */
static inline int wr_iot_terminal_command_quiescent(
 const struct wr_iot_terminal_command_owner *s, unsigned long generation)
{
 if(!s || !generation || s->generation!=generation || !s->closed ||
    s->joining || s->attaching)return 0;
 return s->joined || s->attempt==0 || s->create_failed;
}
#endif
