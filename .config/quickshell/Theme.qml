pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: root

    property int version: 0

    // File watcher for dynamic theme reloading
    property var colorsJsonFile: FileView {
        path: Quickshell.env("HOME") + "/.config/quickshell/colors.json"
        printErrors: false
        onLoaded: {
            root.version++;
        }
    }

    // Default fallback palette (Nord)
    readonly property color defaultBase: "#2e3440"
    readonly property color defaultMantle: "#242933"
    readonly property color defaultCrust: "#1e222a"
    readonly property color defaultSurface0: "#3b4252"
    readonly property color defaultSurface1: "#434c5e"
    readonly property color defaultSurface2: "#4c566a"
    readonly property color defaultOverlay0: "#616e88"
    readonly property color defaultOverlay1: "#707d97"
    readonly property color defaultText: "#eceff4"
    readonly property color defaultSubtext0: "#d8dee9"
    readonly property color defaultSubtext1: "#e5e9f0"
    readonly property color defaultBlue: "#81a1c1"
    readonly property color defaultLavender: "#88c0d0"
    readonly property color defaultSapphire: "#5e81ac"
    readonly property color defaultTeal: "#8fbcbb"
    readonly property color defaultGreen: "#a3be8c"
    readonly property color defaultYellow: "#ebcb8b"
    readonly property color defaultPeach: "#d08770"
    readonly property color defaultRed: "#bf616a"
    readonly property color defaultMauve: "#b48ead"
    readonly property color defaultAccent: "#88c0d0"

    // Raw loaded map
    property var colorMap: {
        var v = root.version;
        try {
            var raw = colorsJsonFile.text();
            if (raw && raw.trim().length > 0) {
                return JSON.parse(raw);
            }
        } catch (e) {
            // fallback
        }
        return {};
    }

    function parseColor(str, fallback) {
        if (!str || typeof str !== "string") return fallback;
        str = str.trim();
        if (str.startsWith("#")) return str;
        // Parse rgba(r, g, b, a) or rgb(r, g, b)
        var m = str.match(/^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)$/);
        if (m) {
            var r = parseInt(m[1], 10) / 255.0;
            var g = parseInt(m[2], 10) / 255.0;
            var b = parseInt(m[3], 10) / 255.0;
            var a = m[4] !== undefined ? parseFloat(m[4]) : 1.0;
            return Qt.rgba(r, g, b, a);
        }
        return fallback;
    }

    function getColor(name, fallback) {
        if (colorMap && colorMap[name]) {
            return parseColor(colorMap[name], fallback);
        }
        return fallback;
    }

    // Semantic Colors
    property color base: getColor("base", defaultBase)
    property color mantle: getColor("mantle", defaultMantle)
    property color crust: getColor("crust", defaultCrust)
    property color surface0: getColor("surface0", defaultSurface0)
    property color surface1: getColor("surface1", defaultSurface1)
    property color surface2: getColor("surface2", defaultSurface2)
    property color overlay0: getColor("overlay0", defaultOverlay0)
    property color overlay1: getColor("overlay1", defaultOverlay1)
    property color text: getColor("text", defaultText)
    property color subtext0: getColor("subtext0", defaultSubtext0)
    property color subtext1: getColor("subtext1", defaultSubtext1)
    property color blue: getColor("blue", defaultBlue)
    property color lavender: getColor("lavender", defaultLavender)
    property color sapphire: getColor("sapphire", defaultSapphire)
    property color teal: getColor("teal", defaultTeal)
    property color green: getColor("green", defaultGreen)
    property color yellow: getColor("yellow", defaultYellow)
    property color peach: getColor("peach", defaultPeach)
    property color red: getColor("red", defaultRed)
    property color mauve: getColor("mauve", defaultMauve)
    property color accent: getColor("accent", defaultAccent)

    // Dynamic Glassmorphic Colors matching Waybar
    property color barBg: getColor("waybar_bg", Qt.rgba(30/255, 34/255, 42/255, 0.60))
    property color barBorder: getColor("waybar_border", Qt.rgba(1, 1, 1, 0.12))
    property color barShadow: getColor("waybar_shadow", Qt.rgba(0, 0, 0, 0.40))

    property color moduleBg: getColor("module_bg", Qt.rgba(46/255, 52/255, 64/255, 0.88))
    property color moduleBorder: getColor("module_border", Qt.rgba(1, 1, 1, 0.12))
    property color moduleHoverBg: getColor("module_hover_bg", Qt.rgba(59/255, 66/255, 82/255, 0.95))
    property color moduleHoverBorder: getColor("module_hover_border", Qt.rgba(136/255, 192/255, 208/255, 0.50))
    property color moduleActiveBg: getColor("module_active_bg", Qt.rgba(67/255, 76/255, 94/255, 0.80))
    property color accentGlow: getColor("accent_glow", Qt.rgba(136/255, 192/255, 208/255, 0.40))

    property color tooltipBg: getColor("tooltip_bg", Qt.rgba(36/255, 41/255, 51/255, 0.95))
    property color tooltipBorder: getColor("tooltip_border", Qt.rgba(136/255, 192/255, 208/255, 0.45))

    // Typography & Metrics
    readonly property string fontFamily: "JetBrainsMono Nerd Font, JetBrains Mono, monospace"
    readonly property int fontSizeSmall: 11
    readonly property int fontSize: 13
    readonly property int fontSizeLarge: 15
    readonly property int fontSizeIcon: 16

    readonly property int barHeight: 38
    readonly property int barRadius: 16
    readonly property int capsuleRadius: 12
    readonly property int pillRadius: 8
}
