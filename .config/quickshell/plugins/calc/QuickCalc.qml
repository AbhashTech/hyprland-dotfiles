import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 440
    implicitHeight: 200
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property string calculationResult: ""
    property string calculationError: ""

    function evaluateExpression(expr) {
        root.calculationError = "";
        expr = expr.trim();
        if (!expr) {
            root.calculationResult = "";
            return;
        }

        try {
            // Safe evaluation using JS Math
            var clean = expr.replace(/\^/g, "**").replace(/x/g, "*").replace(/X/g, "*").replace(/÷/g, "/");
            // Inject Math scope
            var scope = "var sin = Math.sin, cos = Math.cos, tan = Math.tan, sqrt = Math.sqrt, abs = Math.abs, round = Math.round, floor = Math.floor, ceil = Math.ceil, PI = Math.PI, pi = Math.PI, E = Math.E, log = Math.log, pow = Math.pow;";
            var res = Function(scope + " return (" + clean + ");")();
            if (typeof res === "number") {
                if (isNaN(res) || !isFinite(res)) {
                    root.calculationError = "Invalid calculation";
                    root.calculationResult = "";
                } else {
                    root.calculationResult = String(res);
                }
            } else {
                root.calculationResult = String(res);
            }
        } catch (e) {
            root.calculationError = "Expression error";
            root.calculationResult = "";
        }
    }

    function copyResult() {
        if (root.calculationResult) {
            copyProc.exec(["bash", "-c", "wl-copy '" + root.calculationResult + "' && (command -v wtype >/dev/null 2>&1 && wtype -M ctrl -k v -m ctrl || true)"]);
            PluginManager.closeAll();
        }
    }

    Process {
        id: copyProc
    }

    Component.onCompleted: calcInput.forceActiveFocus()

    Connections {
        target: PluginManager
        function onCalcVisibleChanged() {
            if (PluginManager.calcVisible) {
                calcInput.text = "";
                root.calculationResult = "";
                root.calculationError = "";
                calcInput.forceActiveFocus();
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // Header
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: " Quick Calculator"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                color: Theme.accent
            }

            Item { Layout.fillWidth: true }

            Text {
                text: "Esc to close"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }

        // Expression Input
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 46
            radius: Theme.pillRadius
            color: Theme.moduleBg
            border.color: calcInput.activeFocus ? Theme.accent : Theme.moduleBorder
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 8

                Text {
                    text: "="
                    font.family: Theme.fontFamily
                    font.pixelSize: 20
                    font.bold: true
                    color: Theme.accent
                }

                TextInput {
                    id: calcInput
                    Layout.fillWidth: true
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeLarge
                    color: Theme.text
                    selectByMouse: true

                    Text {
                        text: "e.g. (120 * 4) + sqrt(144) or 2^8"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.overlay0
                        visible: !calcInput.text && !calcInput.activeFocus
                    }

                    onTextChanged: root.evaluateExpression(calcInput.text)
                    Keys.onEscapePressed: PluginManager.closeAll()
                    Keys.onReturnPressed: root.copyResult()
                }
            }
        }

        // Result Container
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: Theme.pillRadius
            color: Theme.surface0
            border.color: Theme.surface1
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16

                Text {
                    text: root.calculationError ? root.calculationError : (root.calculationResult ? root.calculationResult : "Result will appear here")
                    font.family: Theme.fontFamily
                    font.pixelSize: 18
                    font.bold: true
                    color: root.calculationError ? Theme.red : (root.calculationResult ? Theme.accent : Theme.overlay0)
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }

                Rectangle {
                    visible: root.calculationResult.length > 0
                    implicitWidth: copyText.implicitWidth + 14
                    implicitHeight: 28
                    radius: 6
                    color: copyArea.containsMouse ? Theme.accent : Theme.moduleBg
                    border.color: Theme.accent
                    border.width: 1

                    Text {
                        id: copyText
                        anchors.centerIn: parent
                        text: "󰆏 Copy"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold: true
                        color: copyArea.containsMouse ? Theme.crust : Theme.accent
                    }

                    MouseArea {
                        id: copyArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.copyResult()
                    }
                }
            }
        }
    }
}
