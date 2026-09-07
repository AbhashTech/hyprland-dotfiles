import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 560
    implicitHeight: 460
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property var allEmojis: []
    property var filteredEmojis: []
    property int selectedIndex: 0

    function loadDefaultEmojis() {
        var list = [
            { char: "😀", name: "Grinning Face", tags: "smile happy grin" },
            { char: "😃", name: "Big Eyes", tags: "smile happy joy" },
            { char: "😄", name: "Smiling Eyes", tags: "smile happy joy laugh" },
            { char: "😁", name: "Beaming Face", tags: "grin happy smile" },
            { char: "😆", name: "Squinting Face", tags: "laugh haha lol" },
            { char: "😅", name: "Sweat Smile", tags: "hot nervous phew" },
            { char: "🤣", name: "ROFL", tags: "rofl lol haha lmao" },
            { char: "😂", name: "Joy Tears", tags: "laugh haha lol cry joy" },
            { char: "🙂", name: "Slight Smile", tags: "smile ok fine" },
            { char: "🙃", name: "Upside Down", tags: "sarcasm silly" },
            { char: "😉", name: "Wink", tags: "wink flirt joke" },
            { char: "😊", name: "Blush", tags: "blush happy warm" },
            { char: "😇", name: "Halo Angel", tags: "angel innocent pure" },
            { char: "🥰", name: "Hearts Face", tags: "love affection adore" },
            { char: "😍", name: "Heart Eyes", tags: "love romance crush" },
            { char: "🤩", name: "Star Struck", tags: "excited wow amazing" },
            { char: "😘", name: "Blow Kiss", tags: "kiss love romance" },
            { char: "😋", name: "Yummy", tags: "delicious yummy nom" },
            { char: "😛", name: "Tongue", tags: "tongue silly playful" },
            { char: "😜", name: "Wink Tongue", tags: "playful silly crazy" },
            { char: "🤪", name: "Zany Face", tags: "wild party goofy" },
            { char: "😎", name: "Sunglasses", tags: "cool swag awesome" },
            { char: "🤓", name: "Nerd", tags: "geek smart glasses" },
            { char: "🧐", name: "Monocle", tags: "curious inspect classy" },
            { char: "🤔", name: "Thinking", tags: "hmm wonder ponder" },
            { char: "🤐", name: "Zipper Mouth", tags: "silent secret quiet" },
            { char: "🤨", name: "Raised Eyebrow", tags: "suspicious doubt" },
            { char: "😐", name: "Neutral", tags: "meh pokerface straight" },
            { char: "😑", name: "Expressionless", tags: "deadpan blank" },
            { char: "😶", name: "No Mouth", tags: "speechless silence" },
            { char: "😏", name: "Smirk", tags: "smirk playful confident" },
            { char: "😒", name: "Unamused", tags: "annoyed dissatisfied" },
            { char: "🙄", name: "Rolling Eyes", tags: "eyeroll bored" },
            { char: "😬", name: "Grimace", tags: "awkward nervous cringe" },
            { char: "🤥", name: "Liar", tags: "pinocchio dishonest" },
            { char: "😌", name: "Relieved", tags: "peace calm chill" },
            { char: "😔", name: "Pensive", tags: "sad down" },
            { char: "😪", name: "Sleepy", tags: "tired sleep yawn" },
            { char: "😴", name: "Sleeping", tags: "zzz tired goodnight" },
            { char: "😷", name: "Mask", tags: "sick illness flu" },
            { char: "🤯", name: "Exploding Head", tags: "mind blown shock" },
            { char: "🥳", name: "Partying", tags: "party birthday yay" },
            { char: "🥺", name: "Pleading", tags: "puppy eyes please" },
            { char: "😭", name: "Loudly Crying", tags: "sob tears scream" },
            { char: "😱", name: "Screaming", tags: "horror terror scream" },
            { char: "😡", name: "Enraged", tags: "angry mad fury red" },
            { char: "💀", name: "Skull", tags: "dead skeleton danger lol" },
            { char: "💩", name: "Poop", tags: "poop crap joke" },
            { char: "🤡", name: "Clown", tags: "clown fool funny" },
            { char: "👻", name: "Ghost", tags: "spooky boo halloween" },
            { char: "👽", name: "Alien", tags: "ufo extraterrestrial" },
            { char: "🤖", name: "Robot", tags: "bot ai tech machine" },
            { char: "👋", name: "Waving Hand", tags: "hello bye hi wave" },
            { char: "👌", name: "OK Hand", tags: "perfect alright good" },
            { char: "✌️", name: "Victory", tags: "peace two victory v" },
            { char: "🤞", name: "Crossed Fingers", tags: "luck hope wish" },
            { char: "🤟", name: "Love You", tags: "ily love rock hand" },
            { char: "🤘", name: "Horns Sign", tags: "rock metal concert" },
            { char: "🤙", name: "Call Me", tags: "shaka phone hang loose" },
            { char: "👍", name: "Thumbs Up", tags: "like approve good yes +1" },
            { char: "👎", name: "Thumbs Down", tags: "dislike bad no -1" },
            { char: "👏", name: "Clapping", tags: "applause cheer bravo" },
            { char: "🙌", name: "Raising Hands", tags: "celebrate praise hooray" },
            { char: "🤝", name: "Handshake", tags: "deal partner agreement" },
            { char: "🙏", name: "Folded Hands", tags: "please pray thanks namaste" },
            { char: "💪", name: "Biceps", tags: "muscle strong gym power" },
            { char: "❤️", name: "Red Heart", tags: "love passion romance like" },
            { char: "🧡", name: "Orange Heart", tags: "warmth friendship" },
            { char: "💛", name: "Yellow Heart", tags: "joy sunshine" },
            { char: "💚", name: "Green Heart", tags: "nature health" },
            { char: "💙", name: "Blue Heart", tags: "trust peace loyalty" },
            { char: "💜", name: "Purple Heart", tags: "royalty luxury charm" },
            { char: "🖤", name: "Black Heart", tags: "dark goth sorrow" },
            { char: "🤍", name: "White Heart", tags: "pure clean peace" },
            { char: "💔", name: "Broken Heart", tags: "sad heartbreak sorrow" },
            { char: "🔥", name: "Fire", tags: "lit hot burn awesome flame" },
            { char: "✨", name: "Sparkles", tags: "magic clean shiny star" },
            { char: "⭐", name: "Star", tags: "rating gold favorite" },
            { char: "⚡", name: "Lightning", tags: "electric power fast energy" },
            { char: "🎉", name: "Party Popper", tags: "celebrate victory birthday" },
            { char: "🚀", name: "Rocket", tags: "launch fast space ship" },
            { char: "💡", name: "Lightbulb", tags: "idea smart inspiration" },
            { char: "💻", name: "Laptop", tags: "computer code tech pc" },
            { char: "☕", name: "Coffee", tags: "tea drink caffeine morning" },
            { char: "🍕", name: "Pizza", tags: "food slice cheese" },
            { char: "✅", name: "Check Mark", tags: "done pass ok success" },
            { char: "❌", name: "Cross Mark", tags: "fail wrong no error" },
            { char: "⚠️", name: "Warning", tags: "alert caution danger" }
        ];
        root.allEmojis = list;
        root.filterEmojis();
    }

    function filterEmojis() {
        var q = emojiInput.text.toLowerCase().trim();
        var list = [];
        for (var i = 0; i < root.allEmojis.length; i++) {
            var em = root.allEmojis[i];
            if (q.length === 0 || em.name.toLowerCase().indexOf(q) !== -1 || em.tags.toLowerCase().indexOf(q) !== -1) {
                list.push(em);
            }
        }
        root.filteredEmojis = list;
        root.selectedIndex = 0;
    }

    function copyEmoji(em) {
        if (!em) return;
        PluginManager.closeAll();
        copyProc.exec(["bash", "-c", "wl-copy '" + em.char + "' && (command -v wtype >/dev/null 2>&1 && wtype '" + em.char + "' || true)"]);
    }

    Process {
        id: copyProc
    }

    focus: true
    Keys.onEscapePressed: event => {
        PluginManager.closeAll();
        event.accepted = true;
    }

    function grabFocus() {
        emojiInput.text = "";
        root.filterEmojis();
        emojiInput.forceActiveFocus();
    }

    Component.onCompleted: {
        root.loadDefaultEmojis();
        root.grabFocus();
    }

    Connections {
        target: PluginManager
        function onEmojiVisibleChanged() {
            if (PluginManager.emojiVisible) {
                root.grabFocus();
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // Header & Search
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 42
                radius: Theme.pillRadius
                color: Theme.moduleBg
                border.color: emojiInput.activeFocus ? Theme.accent : Theme.moduleBorder
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 8

                    Text {
                        text: "󰞅"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeIcon
                        color: Theme.accent
                    }

                    TextInput {
                        id: emojiInput
                        Layout.fillWidth: true
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.text

                        Text {
                            text: "Search emojis by name or keyword..."
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: Theme.overlay0
                            visible: !emojiInput.text && !emojiInput.activeFocus
                        }

                        onTextChanged: root.filterEmojis()
                        Keys.onEscapePressed: PluginManager.closeAll()
                        Keys.onReturnPressed: {
                            if (root.filteredEmojis.length > 0 && root.selectedIndex >= 0) {
                                root.copyEmoji(root.filteredEmojis[root.selectedIndex]);
                            }
                        }
                        Keys.onRightPressed: {
                            if (root.selectedIndex < root.filteredEmojis.length - 1) {
                                root.selectedIndex++;
                                emojiGrid.positionViewAtIndex(root.selectedIndex, GridView.Contain);
                            }
                        }
                        Keys.onLeftPressed: {
                            if (root.selectedIndex > 0) {
                                root.selectedIndex--;
                                emojiGrid.positionViewAtIndex(root.selectedIndex, GridView.Contain);
                            }
                        }
                        Keys.onDownPressed: {
                            var cols = Math.max(1, Math.floor(emojiGrid.width / 64));
                            if (root.selectedIndex + cols < root.filteredEmojis.length) {
                                root.selectedIndex += cols;
                                emojiGrid.positionViewAtIndex(root.selectedIndex, GridView.Contain);
                            }
                        }
                        Keys.onUpPressed: {
                            var cols = Math.max(1, Math.floor(emojiGrid.width / 64));
                            if (root.selectedIndex - cols >= 0) {
                                root.selectedIndex -= cols;
                                emojiGrid.positionViewAtIndex(root.selectedIndex, GridView.Contain);
                            }
                        }
                    }
                }
            }
        }

        // Emoji Grid
        GridView {
            id: emojiGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            cellWidth: 64
            cellHeight: 64
            model: root.filteredEmojis

            delegate: Rectangle {
                id: emojiCell
                required property var modelData
                required property int index

                width: 58
                height: 58
                radius: Theme.pillRadius
                color: root.selectedIndex === index ? Theme.moduleHoverBg : Theme.moduleBg
                border.color: root.selectedIndex === index ? Theme.accent : Theme.moduleBorder
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: modelData.char
                    font.pixelSize: 26
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onEntered: root.selectedIndex = index
                    onClicked: root.copyEmoji(modelData)
                }
            }
        }

        // Status Row
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: root.filteredEmojis.length > 0 && root.selectedIndex < root.filteredEmojis.length ? root.filteredEmojis[root.selectedIndex].name : ""
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.accent
            }

            Item { Layout.fillWidth: true }

            Text {
                text: "Click or Enter to Paste • Esc to close"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }
    }
}
