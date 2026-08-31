#!/usr/bin/env bash
# =============================================================================
# Hide Non-User / Technical / Helper Apps from Application Launchers
# =============================================================================

set -e

APPS_DIR="${HOME}/.local/share/applications"
mkdir -p "${APPS_DIR}"

UNWANTED_APPS=(
    # Avahi & Network debugging tools
    "avahi-discover.desktop"
    "bssh.desktop"
    "bvnc.desktop"
    "cups.desktop"
    "ktelnetservice6.desktop"
    "xgps.desktop"
    "xgpsspeed.desktop"

    # Geo-handlers & URI redirection tools
    "google-maps-geo-handler.desktop"
    "openstreetmap-geo-handler.desktop"
    "wheelmap-geo-handler.desktop"

    # Hardware, topology & V4L2 capture testers
    "lstopo.desktop"
    "qv4l2.desktop"
    "qvidcap.desktop"
    "org.freedesktop.Xwayland.desktop"

    # Smartcard, security helpers & portal agents
    "gcr-prompter.desktop"
    "gcr-viewer.desktop"
    "gscriptor.desktop"
    "org.gnupg.pinentry-qt.desktop"
    "polkit-gnome-authentication-agent-1.desktop"
    "xdg-desktop-portal-gtk.desktop"

    # KDE internal KCM modules and background daemons
    "kcm_netpref.desktop"
    "kcm_proxy.desktop"
    "kcm_trash.desktop"
    "kcm_webshortcuts.desktop"
    "org.kde.kiod6.desktop"
    "org.kde.knewstuff-dialog6.desktop"
    "org.kde.ksecretd.desktop"

    # Redundant entries & sub-handlers
    "kitty-open.desktop"
    "org.pwmt.zathura-pdf-mupdf.desktop"
)

echo "Hiding technical and internal background apps from app launchers..."

for app in "${UNWANTED_APPS[@]}"; do
    SRC="/usr/share/applications/${app}"
    DEST="${APPS_DIR}/${app}"

    if [ -f "${SRC}" ]; then
        cp "${SRC}" "${DEST}"
        if ! grep -q "^NoDisplay=" "${DEST}"; then
            echo "NoDisplay=true" >> "${DEST}"
        else
            sed -i 's/^NoDisplay=.*/NoDisplay=true/' "${DEST}"
        fi
        echo "  ✔ Hidden: ${app}"
    fi
done

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APPS_DIR}" >/dev/null 2>&1 || true
fi

echo "App menu cleanup complete."
