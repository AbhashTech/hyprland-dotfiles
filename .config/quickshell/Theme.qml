pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: root

    // File watcher for dynamic theme reloading
    property var colorsJsonFile: FileView {
        path: Quickshell.env("HOME") + "/.config/quickshell/colors.json"
        printErrors: false
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

    function getColor(name, fallback) {
        if (colorMap && colorMap[name]) {
            return colorMap[name];
        }
        return fallback;
    }

    // Semantic Colors
    readonly property color base: getColor("base", defaultBase)
    readonly property color mantle: getColor("mantle", defaultMantle)
    readonly property color crust: getColor("crust", defaultCrust)
    readonly property color surface0: getColor("surface0", defaultSurface0)
    readonly property color surface1: getColor("surface1", defaultSurface1)
    readonly property color surface2: getColor("surface2", defaultSurface2)
    readonly property color overlay0: getColor("overlay0", defaultOverlay0)
    readonly property color overlay1: getColor("overlay1", defaultOverlay1)
    readonly property color text: getColor("text", defaultText)
    readonly property color subtext0: getColor("subtext0", defaultSubtext0)
    readonly property color subtext1: getColor("subtext1", defaultSubtext1)
    readonly property color blue: getColor("blue", defaultBlue)
    readonly property color lavender: getColor("lavender", defaultLavender)
    readonly property color sapphire: getColor("sapphire", defaultSapphire)
    readonly property color teal: getColor("teal", defaultTeal)
    readonly property color green: getColor("green", defaultGreen)
    readonly property color yellow: getColor("yellow", defaultYellow)
    readonly property color peach: getColor("peach", defaultPeach)
    readonly property color red: getColor("red", defaultRed)
    readonly property color mauve: getColor("mauve", defaultMauve)
    readonly property color accent: getColor("accent", defaultAccent)

    // Dynamic Glassmorphic Colors matching Waybar
    readonly property color barBg: getColor("waybar_bg", "#991e222a")
    readonly property color barBorder: getColor("waybar_border", "#1fffffff")
    readonly property color barShadow: getColor("waybar_shadow", "#66000000")

    readonly property color moduleBg: getColor("module_bg", "#e02e3440")
    readonly property color moduleBorder: getColor("module_border", "#1fffffff")
    readonly property color moduleHoverBg: getColor("module_hover_bg", "#f23b4252")
    readonly property color moduleHoverBorder: getColor("module_hover_border", "#8088c0d0")
    readonly property color moduleActiveBg: getColor("module_active_bg", "#cc434c5e")
    readonly property color accentGlow: getColor("accent_glow", "#6688c0d0")

    readonly property color tooltipBg: getColor("tooltip_bg", "#f2242933")
    readonly property color tooltipBorder: getColor("tooltip_border", "#7388c0d0")

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
