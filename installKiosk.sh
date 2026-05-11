#!/bin/bash
# installKiosk.sh - Deploy Bravil UI as fullscreen Chromium kiosk on Raspberry Pi 5.
# Run with: sudo ./installKiosk.sh
#
# Idempotent. Re-running overwrites the launcher and autostart entry.

set -euo pipefail

USER_NAME="${SUDO_USER:-$USER}"
USER_HOME=$(getent passwd "$USER_NAME" | cut -d: -f6)
LAUNCHER="$USER_HOME/.local/bin/bravilKiosk.sh"
AUTOSTART_DIR="$USER_HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/bravil-kiosk.desktop"
KIOSK_PROFILE="$USER_HOME/.config/bravilKiosk"
UI_PATH="$USER_HOME/printer_data/config/klipper-control.html"
KIOSK_URL="file://$UI_PATH"

step() { printf '\n\033[1;33m== %s ==\033[0m\n' "$*"; }

if [ "$EUID" -ne 0 ]; then
    echo "Run with sudo: sudo $0"
    exit 1
fi

# 1. Packages
step "Installing packages"
apt-get update
apt-get install -y chromium-browser onboard unclutter curl xdotool

# 2. Launcher
step "Writing launcher to $LAUNCHER"
mkdir -p "$(dirname "$LAUNCHER")"
cat >"$LAUNCHER" <<EOF
#!/bin/bash
# Bravil kiosk launcher. Waits for Moonraker, disables blanking, opens UI.

KIOSK_URL="$KIOSK_URL"
PROFILE="$KIOSK_PROFILE"

log() { logger -t bravilKiosk "\$*"; echo "[bravilKiosk] \$*"; }

log "waiting for Moonraker (up to 60 s)"
for i in \$(seq 1 60); do
    if curl -sf --max-time 1 http://localhost:7125/printer/info >/dev/null 2>&1; then
        log "Moonraker up after \${i}s"
        break
    fi
    sleep 1
done

log "disabling screen blanking + DPMS"
xset s off s noblank
xset -dpms

log "starting unclutter"
unclutter -idle 1 -root &

log "starting onboard (on-screen keyboard)"
onboard --layout=Phone --theme=Nightshade &

log "launching Chromium in kiosk mode -> \$KIOSK_URL"
exec chromium-browser \\
    --kiosk \\
    --noerrdialogs \\
    --disable-infobars \\
    --disable-translate \\
    --disable-features=TranslateUI \\
    --disable-pinch \\
    --overscroll-history-navigation=0 \\
    --check-for-update-interval=31536000 \\
    --user-data-dir="\$PROFILE" \\
    "\$KIOSK_URL"
EOF
chmod +x "$LAUNCHER"
chown "$USER_NAME:$USER_NAME" "$LAUNCHER"

# 3. Autostart
step "Registering autostart at $AUTOSTART_FILE"
mkdir -p "$AUTOSTART_DIR"
cat >"$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Bravil Kiosk
Exec=$LAUNCHER
X-GNOME-Autostart-enabled=true
NoDisplay=false
Terminal=false
EOF
chown -R "$USER_NAME:$USER_NAME" "$AUTOSTART_DIR"

# 4. Verify UI file
if [ ! -f "$UI_PATH" ]; then
    step "WARNING"
    echo "UI file not found at $UI_PATH"
    echo "Copy klipper-control.html there before next boot."
fi

step "Done"
echo "Reboot to verify autostart, or run the launcher manually:"
echo "    $LAUNCHER"
echo
echo "Exit kiosk: long-press Bravil badge for 3s, or from SSH: pkill chromium"
