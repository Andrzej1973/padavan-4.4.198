#ifndef WR_BAND_LIFECYCLE_H
#define WR_BAND_LIFECYCLE_H
enum wr_band_apply_state { WR_APPLY_REJECTED, WR_APPLY_OFF_UNVERIFIED,
    WR_APPLY_OFF_CONFIRMED, WR_APPLY_PROFILE_ERROR, WR_APPLY_START_ERROR,
    WR_APPLY_RUNNING };
struct wr_band_lifecycle_ops {
    int (*validate_snapshot)(void *);
    /* Success requires both drivers OFF and no competing daemon owner.
     * A sent STOP, missing PID/socket or elapsed timeout is not success. */
    int (*quiesce_verified)(void *);
    /* Both profiles must use the same serialized settings snapshot. */
    int (*write_both_profiles)(void *, int enabled);
    int (*initialize_both_radios)(void *);
    /* Success requires ready/enabled driver acknowledgements for both bands. */
    int (*start_verified)(void *);
};
struct wr_band_apply_result { enum wr_band_apply_state state; int off_confirmed; };
/* Caller holds settings/lifecycle serialization for the entire call. No rc
 * binding is supplied here. Callbacks return exactly zero for success. */
int wr_band_lifecycle_apply(const struct wr_band_lifecycle_ops *, void *, int enabled,
                            struct wr_band_apply_result *);
#endif
