import QtQuick
import Quickshell
import Quickshell.Services.Mpris
import ".."

Rectangle {
    id: root

    property var barWindow: null
    property string barSection: "center"
    property int barIndex: -1
    property var barContainer: null

    readonly property var activePlayer: {
        const list = Mpris.players.values;
        if (!list || list.length === 0) return null;
        for (let i = 0; i < list.length; i++) {
            if (list[i] && list[i].playbackState === MprisPlaybackState.Playing) return list[i];
        }
        return list[0] || null;
    }

    readonly property bool isPlaying: activePlayer ? activePlayer.playbackState === MprisPlaybackState.Playing : false

    readonly property string fullMediaText: {
        if (!activePlayer) return "";
        const title = (activePlayer.trackTitle || "").trim();
        const artist = (activePlayer.trackArtist || (activePlayer.trackArtists && activePlayer.trackArtists.length > 0 ? activePlayer.trackArtists.join(", ") : "")).trim();
        if (artist && title) return `${artist} - ${title}`;
        if (title) return title;
        if (artist) return artist;
        return "";
    }

    readonly property string mediaText: {
        const raw = fullMediaText;
        if (raw.length > 26) {
            return raw.substring(0, 23) + "...";
        }
        return raw;
    }

    readonly property bool hasMedia: mediaText.length > 0

    visible: hasMedia
    implicitHeight: Theme.barHeight - 8
    implicitWidth: visible ? Math.min(row.implicitWidth + 14, 220) : 0
    radius: Theme.capsuleRadius

    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    Behavior on implicitWidth { NumberAnimation { duration: 150 } }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered && !BarConfig.isDragging
        icon: root.isPlaying ? "󰐊" : "󰏤"
        iconColor: root.isPlaying ? Theme.green : Theme.subtext0
        title: root.fullMediaText !== "" ? root.fullMediaText : "Media Player"
        description: root.isPlaying ? "Currently Playing" : "Playback Paused"
        shortcuts: [
            { action: "Play / Pause", key: "Left Click" },
            { action: "Next Track", key: "Scroll Up" },
            { action: "Previous Track", key: "Scroll Down" }
        ]
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 4

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.isPlaying ? "󰐊" : "󰏤"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: root.isPlaying ? Theme.green : Theme.subtext0
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.mediaText
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            font.italic: !root.isPlaying
            color: Theme.text
            elide: Text.ElideRight
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: BarConfig.isDragging ? Qt.ClosedHandCursor : Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        property real pressX: 0
        property real pressY: 0
        property bool didDrag: false

        onPressed: mouse => {
            pressX = mouse.x;
            pressY = mouse.y;
            didDrag = false;
        }

        onPositionChanged: mouse => {
            if (pressed && mouse.buttons === Qt.LeftButton) {
                var dx = mouse.x - pressX;
                var dy = mouse.y - pressY;
                if (!didDrag && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
                    didDrag = true;
                    BarConfig.startDrag("mpris", root.barSection, root.barIndex);
                }
                if (didDrag && root.barContainer) {
                    var pt = mapToItem(root.barContainer, mouse.x, mouse.y);
                    BarConfig.updateDragPos(pt.x, root.barContainer.width);
                }
            }
        }

        onReleased: mouse => {
            if (didDrag) {
                BarConfig.endDrag();
                didDrag = false;
            } else if (mouse.button === Qt.LeftButton) {
                if (root.activePlayer) {
                    root.activePlayer.togglePlaying();
                }
            }
        }

        onWheel: wheel => {
            if (!root.activePlayer) return;
            if (wheel.angleDelta.y > 0) {
                root.activePlayer.next();
            } else if (wheel.angleDelta.y < 0) {
                root.activePlayer.previous();
            }
        }
    }
}
