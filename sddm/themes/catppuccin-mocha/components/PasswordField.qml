import QtQuick
import QtQuick.Controls

Item {
    id: passwordFieldRoot

    property alias text: passwordInput.text
    property string placeholder: "Password"
    property color textColor: "#ffffff"
    property color placeholderColor: "#a6adc8"
    property color accentColor: "#cba6f7"
    property color errorColor: "#f38ba8"
    property color bgBaseColor: Qt.rgba(20/255, 20/255, 30/255, 0.45)
    property color bgFocusColor: Qt.rgba(35/255, 35/255, 50/255, 0.7)
    property bool isLoggingIn: false
    property bool hasError: false
    property bool isPasswordHidden: true

    signal submitted()

    implicitWidth: 320
    implicitHeight: 46

    function focusInput() {
        passwordInput.forceActiveFocus()
    }

    function triggerShake() {
        shakeAnimation.restart()
    }

    SequentialAnimation {
        id: shakeAnimation
        NumberAnimation { target: inputContainer; property: "x"; to: -12; duration: 50; easing.type: Easing.InOutQuad }
        NumberAnimation { target: inputContainer; property: "x"; to: 12; duration: 50; easing.type: Easing.InOutQuad }
        NumberAnimation { target: inputContainer; property: "x"; to: -8; duration: 50; easing.type: Easing.InOutQuad }
        NumberAnimation { target: inputContainer; property: "x"; to: 8; duration: 50; easing.type: Easing.InOutQuad }
        NumberAnimation { target: inputContainer; property: "x"; to: -4; duration: 50; easing.type: Easing.InOutQuad }
        NumberAnimation { target: inputContainer; property: "x"; to: 0; duration: 50; easing.type: Easing.InOutQuad }
    }

    Rectangle {
        id: inputContainer
        anchors.fill: parent
        radius: 23
        color: passwordInput.activeFocus ? passwordFieldRoot.bgFocusColor : passwordFieldRoot.bgBaseColor
        border.color: passwordFieldRoot.hasError ? passwordFieldRoot.errorColor
                                                 : (passwordInput.activeFocus ? passwordFieldRoot.accentColor : Qt.rgba(255/255, 255/255, 255/255, 0.5))
        border.width: passwordInput.activeFocus || passwordFieldRoot.hasError ? 2 : 1.2

        Behavior on color { ColorAnimation { duration: 150 } }
        Behavior on border.color { ColorAnimation { duration: 150 } }

        Row {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 16
            spacing: 10

            // Input Box
            TextInput {
                id: passwordInput
                width: parent.width - (eyeToggle.visible ? 28 : 0)
                height: parent.height
                anchors.verticalCenter: parent.verticalCenter
                verticalAlignment: TextInput.AlignVCenter
                echoMode: passwordFieldRoot.isPasswordHidden ? TextInput.Password : TextInput.Normal
                passwordCharacter: "●"
                color: passwordFieldRoot.textColor
                selectionColor: passwordFieldRoot.accentColor
                selectedTextColor: "#11111b"
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 14
                clip: true
                activeFocusOnTab: true

                onAccepted: {
                    if (passwordInput.text.length > 0 && !passwordFieldRoot.isLoggingIn) {
                        passwordFieldRoot.submitted()
                    }
                }

                Text {
                    id: placeholderText
                    text: passwordFieldRoot.placeholder
                    color: passwordFieldRoot.placeholderColor
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 13
                    anchors.verticalCenter: parent.verticalCenter
                    visible: !passwordInput.text && !passwordInput.inputMethodComposing
                    opacity: 0.65
                }
            }

            // Reveal/Hide Password Button
            Item {
                id: eyeToggle
                width: 22
                height: 22
                anchors.verticalCenter: parent.verticalCenter
                visible: passwordInput.text.length > 0

                Image {
                    anchors.centerIn: parent
                    width: 16
                    height: 16
                    source: passwordFieldRoot.isPasswordHidden ? "../assets/icons/eye.svg" : "../assets/icons/eye-off.svg"
                    fillMode: Image.PreserveAspectFit
                    opacity: eyeMouseArea.containsMouse ? 1.0 : 0.6
                }

                MouseArea {
                    id: eyeMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        passwordFieldRoot.isPasswordHidden = !passwordFieldRoot.isPasswordHidden
                    }
                }
            }
        }
    }
}
