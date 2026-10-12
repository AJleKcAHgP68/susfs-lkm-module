# SPDX-License-Identifier: GPL-2.0-only
# Match the real kernel release, not the Android OS version or spoofable uname.
select_kmi() {
  case "$1" in
    5.10.*-android12-*) echo android12-5.10 ;;
    5.10.*-android13-*) echo android13-5.10 ;;
    5.15.*-android13-*) echo android13-5.15 ;;
    5.15.*-android14-*) echo android14-5.15 ;;
    6.1.*-android14-*) echo android14-6.1 ;;
    6.6.*-android15-*) echo android15-6.6 ;;
    6.12.*-android15-*) echo android16-6.12 ;;
    *) return 1 ;;
  esac
}
