#!/usr/bin/env bash
# Run after normal firmware succeeds; never install this experimental candidate.
set -euo pipefail
trunk="$(realpath "$1")"
compiler="$(realpath "$2")"
results="$(realpath -m "$3")"
for path in .config config.arch linux-4.4.x/.config user/rc/rc user/httpd/httpd; do
  test -s "$trunk/$path"
done
test -x "$compiler"
test ! -e "$results"
mkdir -p "$results"
probe="$(mktemp -d "$RUNNER_TEMP/iot-runtime-link.XXXXXX")"
trap 'find "$probe" -depth -delete' EXIT
mkdir -p "$probe/trunk/user" "$probe/trunk/configs/boards/WR1200JS"
cp -a "$trunk/user/rc" "$trunk/user/httpd" "$trunk/user/ralinkiappd" "$probe/trunk/user/"
cp "$trunk/configs/boards/WR1200JS/l1profile.dat" "$probe/trunk/configs/boards/WR1200JS/"
sha256sum "$trunk/.config" "$trunk/config.arch" "$trunk/linux-4.4.x/.config" \
  "$trunk/user/rc/rc" "$trunk/user/httpd/httpd" > "$results/baseline.sha256"
for stage in rc http control; do
  python3 "tools/iot/prepare-$stage.py" "$probe"
done
python3 tools/iot/prepare-runtime.py "$probe" --native-trunk "$trunk"
python3 -B tools/iot/prepare-runtime-link-map.py "$probe/trunk/user/rc/Makefile" "$results/rc-link-map.txt"
python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["configuration_snapshot_verified"] is True and r["configuration_ram_control_bound"] is True and r["configuration_flash_readback_verified"] is True' "$probe/iot-runtime-source.json"
python3 tools/iot/prepare-iappd-policy-source.py "$probe"
python3 tools/iot/check-iappd-policy-manifest.py "$probe"
python3 tools/iot/check-runtime-source.py "$probe" "$probe/source-check"
python3 tools/iot/prepare-restart-entry-source.py "$probe"
python3 tools/iot/check-restart-entry-manifest.py "$probe"
cross="${compiler%gcc}"
cat > "$probe/Makefile" <<'MAKE'
.DEFAULT_GOAL := iot-runtime-link
include $(ROOTDIR)/versions.inc
FIRMWARE_KERNEL_VER="4.4"
include $(ROOTDIR)/user/Makefile
.PHONY: iot-runtime-link
iot-runtime-link:
	$(MAKE) -C $(IOT_PROBE)/trunk/user/rc clean
	$(MAKE) -C $(IOT_PROBE)/trunk/user/httpd clean
	$(MAKE) -C $(IOT_PROBE)/trunk/user/rc -j2 all
	$(MAKE) -C $(IOT_PROBE)/trunk/user/httpd -j2 all
MAKE
LC_ALL=C make -f "$probe/Makefile" iot-runtime-link ROOTDIR="$trunk" LINUXDIR=linux-4.4.x \
  PROJECT_CONFIG="$trunk/.config" LINUX_CONFIG="$trunk/linux-4.4.x/.config" \
  ARCH_CONFIG="$trunk/config.arch" IOT_PROBE="$probe" \
  CC="$compiler" STRIP="${cross}strip" AR="${cross}ar" \
  2>&1 | tee "$results/build.log"
"${cross}nm" "$probe/trunk/user/rc/wr-iot-saved-config-store.o" > "$results/generation-selector-store-symbols.txt"
"${cross}objdump" -dr "$probe/trunk/user/rc/ralink.o" > "$results/generation-selector-caller-relocations.txt"
python3 -B tools/iot/verify-generation-selector-link.py "$results" \
  --binary "$probe/trunk/user/rc/rc" --output "$results/generation-selector-link.json"
"${cross}nm" "$probe/trunk/user/rc/wr-iot-rc-backend.o" > "$results/backend-symbols.txt"
for entry in config-edit-server:wr_iot_rc_edit_backend_install config-edit-server:wr_iot_rc_edit_view config-edit-server:wr_iot_rc_edit_observed config-view-runtime:wr_iot_rc_view_runtime_install config-view-runtime:wr_iot_rc_view_runtime_close rc-runtime:wr_iot_rc_runtime_register_view control-server:wr_iot_rc_register_edit_backend; do
  unit="${entry%%:*}"
  symbol="${entry#*:}"
  "${cross}nm" "$probe/trunk/user/rc/wr-iot-$unit.o" | grep -Eq "[[:space:]]T[[:space:]]$symbol\$"
done
"${cross}nm" "$probe/trunk/user/httpd/wr-iot-config-view-client.o" | grep -Eq '[[:space:]]T[[:space:]]wr_iot_http_view_read$'
"${cross}nm" "$probe/trunk/user/httpd/wr-iot-control-client.o" | grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_submit_edit$'
for symbol in wr_iot_rc_config_backend_capture wr_iot_rc_config_backend_current wr_iot_rc_initial_restart_start_begin wr_iot_rc_initial_restart_start_progress wr_iot_rc_initial_restart_active_current wr_iot_rc_initial_restart_cancel_progress wr_iot_rc_initial_restart_detach_commit wr_iot_rc_initial_restart_receipt wr_iot_rc_initial_restart_postrelease_current wr_iot_rc_initial_restart_postrelease_shutdown_begin wr_iot_rc_initial_restart_postrelease_shutdown_closed wr_iot_rc_restart_owned wr_iot_activation_execute wr_iot_activation_continue wr_iot_rc_backend_observed wr_iot_activation_prepare_radio_stop wr_iot_rc_quiesce_begin wr_iot_rc_quiesce_advance wr_iot_rc_rebind_begin; do
  grep -Eq "[[:space:]]T[[:space:]]$symbol\$" "$results/backend-symbols.txt"
done
for entry in config-server:wr_iot_rc_config_execute config-server:wr_iot_rc_config_continue config-server:wr_iot_rc_config_terminal_ready config-server:wr_iot_rc_config_observed config-owner:wr_iot_config_owner_begin_admitted config-owner:wr_iot_config_owner_observed config-owner:wr_iot_config_owner_finish saved-config-store:wr_iot_generation_profile_request saved-config-store:wr_iot_generation_profile_enter saved-config-store:wr_iot_generation_profile_leave restart-profile:wr_iot_restart_profile_file_current saved-config-store:wr_iot_generation_config_capture saved-config-store:wr_iot_generation_config_owned saved-config-store:wr_iot_generation_config_current saved-config-store:wr_iot_generation_config_release saved-config-store:wr_iot_saved_config_capture config-save-server:wr_iot_rc_save_backend_install config-save-server:wr_iot_rc_save_observed control-server:wr_iot_rc_register_save_backend config-save-owner:wr_iot_config_save_begin_admitted config-save-owner:wr_iot_config_save_step config-save-owner:wr_iot_config_save_terminal_ready config-save-owner:wr_iot_config_save_observed config-save-owner:wr_iot_config_save_retire flash-worker:wr_iot_flash_worker_begin flash-worker:wr_iot_flash_worker_step flash-worker:wr_iot_flash_worker_retire flash-save-attempt:wr_iot_flash_save_begin flash-save-attempt:wr_iot_flash_save_step flash-save-native:wr_iot_flash_save_snapshot flash-save-native:wr_iot_flash_save_commit_once native-flash-reader:wr_iot_native_flash_compare saved-config-store:wr_iot_saved_store_begin saved-config-store:wr_iot_saved_store_step saved-config-store:wr_iot_saved_record_current initial-restart-entry:wr_iot_initial_restart_entry initial-restart-select:wr_iot_initial_restart_select initial-restart-select:wr_iot_initial_restart_selected_current rc-physical-stop:wr_iot_rc_physical_begin_initial_selected restart-initial-parent:wr_iot_restart_initial_parent_current restart-initial-handoff:wr_iot_restart_initial_handoff_begin restart-initial-handoff:wr_iot_restart_initial_handoff_step restart-initial-handoff:wr_iot_restart_initial_cancel_step restart-initial-handoff:wr_iot_restart_initial_shutdown_step rc-physical-stop:wr_iot_rc_physical_begin_initial_saved radio-stop-fence:wr_iot_radio_stop_fence_end_cleanup_unless_shutdown initial-off:wr_iot_initial_postrelease_current initial-off:wr_iot_initial_main_current rc-physical-stop:wr_iot_rc_physical_begin_initial rc-physical-stop:wr_iot_rc_physical_begin_initial_off rc-physical-stop:wr_iot_rc_physical_initial_off_read rc-physical-stop:wr_iot_rc_physical_initial_release_read rc-initial-stop:wr_iot_rc_initial_stop_begin_shutdown rc-backend:wr_iot_rc_backend_initial_shutdown_prepare rc-backend:wr_iot_rc_backend_shutdown_initial_request initial-off:wr_iot_initial_off_begin_shutdown initial-off:wr_iot_initial_off_request_shutdown rc-initial-stop:wr_iot_rc_initial_stop_begin rc-initial-stop:wr_iot_rc_initial_stop_step rc-initial-stop:wr_iot_rc_initial_stop_released physical-initial-client:wr_iot_physical_initial_call physical-initial-session:wr_iot_initial_physical_session_begin physical-initial-session:wr_iot_initial_physical_session_advance rc-backend:wr_iot_rc_backend_initial_request rc-backend:wr_iot_rc_backend_prepared_initial_request initial-off:wr_iot_initial_off_physical_request rc-normal-shutdown:wr_iot_rc_normal_notification_begin rc-normal-shutdown:wr_iot_rc_normal_notification_end rc-normal-shutdown:wr_iot_rc_normal_shutdown_pending rc-normal-shutdown:wr_iot_rc_normal_shutdown_step rc-normal-shutdown:wr_iot_rc_normal_shutdown_arm_ready rc-normal-shutdown:wr_iot_rc_normal_shutdown_arm_commit rc-normal-shutdown:wr_iot_rc_normal_shutdown_cold_arm_ready rc-normal-shutdown:wr_iot_rc_normal_shutdown_cold_handoff_ready rc-backend:wr_iot_rc_cold_root_routed_handoff rc-backend:wr_iot_rc_backend_applied_route rc-normal-shutdown:wr_iot_rc_normal_shutdown_terminal_arm_ready rc-physical-stop:wr_iot_rc_physical_begin_routed_shutdown rc-physical-stop:wr_iot_rc_physical_shutdown_release_cleanup rc-physical-stop:wr_iot_rc_physical_shutdown_release radio-stop-fence:wr_iot_radio_stop_fence_begin_routed_shutdown rc-backend:wr_iot_rc_cold_postshutdown_release rc-backend:wr_iot_rc_cold_root_final_shutdown restart-terminal-iapp:wr_iot_terminal_iapp_shutdown_drain restart-terminal-iapp:wr_iot_terminal_iapp_shutdown_finish cold-on-root:wr_iot_cold_root_begin cold-on-root:wr_iot_cold_root_step cold-on-root:wr_iot_cold_root_retire cold-on-root-shutdown:wr_iot_cold_root_shutdown cold-on-root-recovery:wr_iot_cold_root_preup_recover cold-on-root-signal:wr_iot_cold_root_signal_step cold-on-scheduler:wr_iot_rc_cold_on_begin cold-on-scheduler:wr_iot_cold_on_pending cold-on-scheduler:wr_iot_cold_on_step cold-on-scheduler:wr_iot_cold_on_retire cold-on-select:wr_iot_cold_select cold-on-entry:wr_iot_cold_on_entry rc-boot:wr_iot_rc_boot_arm rc-boot:wr_iot_rc_boot_pending rc-boot:wr_iot_rc_boot_step control-mailbox:wr_iot_mailbox_submit_initial rc-backend:wr_iot_rc_boot_idle cold-on-postshutdown:wr_iot_cold_postshutdown_begin rc-backend:wr_iot_rc_cold_shutdown_advance rc-backend:wr_iot_rc_cold_shutdown_off_begin rc-backend:wr_iot_rc_cold_shutdown_closed rc-backend:wr_iot_rc_cold_shutdown_rejected cold-on-shutdown:wr_iot_cold_prehandoff_shutdown cold-on-prehandoff:wr_iot_cold_prehandoff_shutdown_current rc-backend:wr_iot_rc_cold_never_started cold-on-disabled:wr_iot_cold_disabled_begin cold-on-disabled-release:wr_iot_cold_disabled_release_begin rc-backend:wr_iot_rc_cold_disabled_parent_release rc-backend:wr_iot_rc_cold_disabled_terminal_begin rc-backend:wr_iot_rc_cold_disabled_terminal_step rc-backend:wr_iot_rc_cold_disabled_terminal_retire rc-backend:wr_iot_rc_cold_parent_release rc-backend:wr_iot_rc_cold_terminal_begin rc-backend:wr_iot_rc_cold_terminal_step rc-backend:wr_iot_rc_cold_terminal_retire rc-backend:wr_iot_rc_cold_start_begin rc-backend:wr_iot_rc_cold_active_current rc-backend:wr_iot_rc_cold_start_progress precreated-down-observe:wr_iot_initial_down_observe cold-on-admission:wr_iot_cold_admission_begin cold-on-generation:wr_iot_cold_generation_begin precreated-down-recovery:wr_iot_initial_down_recovery_current cold-on-recovery:wr_iot_cold_preup_recover cold-on-main:wr_iot_cold_main_begin cold-on-guest:wr_iot_cold_guest_begin cold-on-services:wr_iot_cold_services_begin cold-on-multicast:wr_iot_cold_multicast_begin cold-on-owner:wr_iot_cold_owner_begin cold-on-handoff:wr_iot_cold_handoff_begin cold-on-release:wr_iot_cold_release_begin cold-on-policy:wr_iot_cold_policy_current precreated-down-client:wr_iot_driver_initial_down_read radio-on-admission:wr_iot_on_admission_begin_reload radio-on-owner:wr_iot_rc_radio_on_begin radio-on-owner:wr_iot_radio_on_pending radio-on-owner:wr_iot_radio_on_step radio-on-owner:wr_iot_radio_on_retire rc-mode:wr_iot_rc_radio_on_mode_read radio-on-followup:wr_iot_on_followup_step rc-runtime:wr_iot_rc_radio_on_release radio-on-release:wr_iot_on_release_current radio-on-handoff:wr_iot_on_rebind_current radio-on-handoff:wr_iot_on_restore_handoff radio-on-handoff:wr_iot_on_rebind_step radio-on-aux:wr_iot_on_aux_down_current rc-runtime:wr_iot_rc_radio_on_disabled_release radio-on-followup:wr_iot_on_followup_observed radio-on-disabled:wr_iot_on_disabled_followup radio-on-disabled:wr_iot_on_disabled_release radio-on-disabled:wr_iot_on_disabled_begin radio-on-disabled:wr_iot_on_disabled_current radio-on-disabled:wr_iot_on_disabled_release_current radio-on-restore:wr_iot_on_restore_begin radio-on-restore:wr_iot_on_restore_preup_recover radio-on-restore:wr_iot_on_restore_step radio-on-multicast:wr_iot_on_multicast_begin radio-on-multicast:wr_iot_on_multicast_step radio-on-multicast:wr_iot_on_multicast_observed radio-on-guest:wr_iot_on_guest_begin radio-on-guest:wr_iot_on_guest_step radio-on-services:wr_iot_on_services_begin radio-on-services:wr_iot_on_services_step radio-on-main:wr_iot_on_main_lan_step radio-on-main:wr_iot_on_main_begin radio-on-main:wr_iot_on_main_step radio-on-generation:wr_iot_on_generation_begin radio-on-generation:wr_iot_on_generation_step radio-on-generation:wr_iot_on_generation_origin_current radio-on-generation:wr_iot_on_generation_abort radio-on-admission:wr_iot_on_admission_begin radio-on-admission:wr_iot_on_admission_cancel radio-off-observe:wr_iot_radio_resume_down_observed rc-runtime:wr_iot_rc_radio_off_receipt radio-off-followup:wr_iot_off_followup_finish radio-off-followup:wr_iot_off_followup_final_current radio-off-wan:wr_iot_off_wan_begin radio-off-wan:wr_iot_off_wan_step radio-off-bridge:wr_iot_radio_off_bridge_observed radio-off-bridge:wr_iot_radio_off_bridge_detach radio-off-followup:wr_iot_off_followup_begin radio-off-followup:wr_iot_off_followup_step radio-off-profile:wr_iot_off_profile_begin radio-off-profile:wr_iot_off_profile_step radio-off-profile-check:wr_iot_rc_off_profile_current radio-off-profile-check:wr_iot_off_profile_current radio-off-observe:wr_iot_radio_off_observed rc-physical-stop:wr_iot_rc_physical_off_read rc-runtime:wr_iot_rc_radio_off_begin rc-physical-stop:wr_iot_rc_physical_off_failed radio-off-owner:wr_iot_radio_off_prepare radio-off-owner:wr_iot_radio_off_step radio-off-owner:wr_iot_radio_off_begin radio-off-owner:wr_iot_radio_off_poll radio-off-owner:wr_iot_radio_off_take rc-physical-stop:wr_iot_rc_physical_take_off restart-entry:wr_iot_restart_entry restart-entry:wr_iot_radio_on_entry restart-entry:wr_iot_radio_off_entry rc-mode:wr_iot_rc_radio_on_saved_request physical-stop-client:wr_iot_physical_stop_call physical-stop-down:wr_iot_physical_stop_down physical-stop-session:wr_iot_physical_session_begin physical-stop-session:wr_iot_physical_session_advance rc-physical-stop:wr_iot_rc_physical_begin rc-physical-stop:wr_iot_rc_physical_step rc-physical-stop:wr_iot_rc_physical_restart_ready rc-physical-stop:wr_iot_rc_physical_begin_quiesce rc-physical-stop:wr_iot_rc_physical_prehandoff_cancel rc-physical-stop:wr_iot_rc_physical_premain_cancel rc-physical-stop:wr_iot_rc_physical_resume_cancel rc-physical-stop:wr_iot_rc_physical_resume_finish rc-physical-stop:wr_iot_rc_physical_resume_read physical-rebind-client:wr_iot_physical_rebind_call physical-rebind-controller:wr_iot_rebind_open_submit physical-rebind-controller:wr_iot_rebind_open_current physical-rebind-controller:wr_iot_rebind_configuration_current rebind-start:wr_iot_rebind_start_begin rebind-network:wr_iot_rebind_network_step rebind-rollback:wr_iot_rebind_rollback_step rebind-commit:wr_iot_rebind_commit_step rebind-close:wr_iot_rebind_close_step rebind-closed-rollback:wr_iot_rebind_closed_rollback_step rebind-runner:wr_iot_rebind_runner_begin rebind-runner:wr_iot_rebind_runner_continue rebind-active-stop:wr_iot_rebind_active_stop_begin rebind-active-stop:wr_iot_rebind_active_stop_continue rebind-observe:wr_iot_rebind_active_observed rebind-observe:wr_iot_rebind_off_closed rebind-owner:wr_iot_rebind_owner_begin rebind-owner:wr_iot_rebind_owner_continue rebind-owner:wr_iot_rebind_owner_restart restart-profile:wr_iot_restart_profile_current restart-main-state:wr_iot_restart_main_down restart-generation:wr_iot_restart_generation_rollback_current restart-generation:wr_iot_restart_generation_begin restart-generation:wr_iot_restart_generation_step restart-generation:wr_iot_restart_generation_origin_current restart-main-up:wr_iot_restart_main_up restart-main-controller:wr_iot_restart_main_begin restart-main-controller:wr_iot_restart_main_step restart-main-controller:wr_iot_restart_main_lan_step restart-main-bridge:wr_iot_restart_main_bridge_attach restart-main-bridge:wr_iot_restart_main_bridge_current restart-prehandoff-check:wr_iot_restart_prehandoff_cancel_check restart-cancel-check:wr_iot_restart_restore_preopen_rejected restart-cancel-check:wr_iot_restart_restore_cancel_check restart-finish-check:wr_iot_restart_restore_finish_check restart-restore:wr_iot_restart_restore_rebind_current restart-restore:wr_iot_restart_restore_handoff restart-scheduler:wr_iot_restart_scheduler_begin restart-scheduler:wr_iot_restart_scheduler_step restart-scheduler:wr_iot_restart_scheduler_pending restart-resume-retire:wr_iot_restart_resume_retire restart-resume:wr_iot_restart_resume_begin restart-resume:wr_iot_restart_resume_step restart-resume:wr_iot_restart_resume_shutdown restart-restore:wr_iot_restart_restore_begin restart-restore:wr_iot_restart_restore_step restart-services:wr_iot_restart_services_begin restart-services:wr_iot_restart_services_step restart-guest-controller:wr_iot_restart_guest_begin restart-guest-controller:wr_iot_restart_guest_step restart-guest-up:wr_iot_restart_guest_down restart-guest-up:wr_iot_restart_guest_up restart-guest-up:wr_iot_restart_guest_admin_state restart-guest-bridge:wr_iot_restart_guest_bridge_attach restart-guest-isolation:wr_iot_restart_guest_isolation_prepare; do
  unit="${entry%%:*}"
  symbol="${entry#*:}"
  "${cross}nm" "$probe/trunk/user/rc/wr-iot-$unit.o" > "$results/$unit-symbols.txt"
  grep -Eq "[[:space:]]T[[:space:]]$symbol\$" "$results/$unit-symbols.txt"
done
"${cross}nm" "$probe/trunk/user/rc/net_wifi.o" > "$results/physical-aux-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_physical_aux_down$' "$results/physical-aux-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_radio_off_policy$' "$results/physical-aux-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_radio_off_state$' "$results/physical-aux-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_radio_off_auth$' "$results/physical-aux-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_restart_guest_policy$' "$results/physical-aux-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_restart_generate$' "$results/physical-aux-symbols.txt"
mkdir -p "$probe/staged/usr/sbin"
for role in rc httpd; do
  binary="$probe/trunk/user/$role/$role"
  test -s "$binary"
  "${cross}readelf" -h "$binary" > "$results/$role-elf.txt"
  grep -q 'Machine:.*MIPS' "$results/$role-elf.txt"
  "${cross}readelf" -Ws "$binary" > "$results/$role-symbols.txt"
  if grep -Eq 'UND[[:space:]]+wr_iot_' "$results/$role-symbols.txt"; then
    echo "Unresolved IoT symbol in $role" >&2; exit 1
  fi
  cp "$binary" "$results/$role"
  cp "$binary" "$probe/staged/usr/sbin/$role"
  python3 tools/band-steering/verify-package-closure.py "$probe/staged" "$trunk/romfs" \
    --binary "usr/sbin/$role" --readelf "${cross}readelf" \
    --output "$results/$role-dependency-closure.json"
done
cp "$probe/iot-runtime-source.json" "$results/"
cp "$probe/iot-edit-view-source.json" "$results/"
cp "$probe/iot-iapp-policy-source.json" "$results/"
cp "$probe/iot-restart-entry-source.json" "$results/"
cp "$probe/trunk/user/ralinkiappd/iappd.sh" "$results/iappd-candidate.sh"
sha256sum "$results/rc" "$results/httpd" > "$results/candidate.sha256"
sha256sum -c "$results/baseline.sha256"
printf '%s\n' 'PASS experimental RC/HTTP target link and dependency closure; no image installation or physical acceptance'

grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_restart_service_policy$' "$results/physical-aux-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_restart_service_submit$' "$results/physical-aux-symbols.txt"

grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_restart_auth_process_current$' "$results/physical-aux-symbols.txt"
