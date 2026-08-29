import QtQuick
import QtQuick.Controls

Item {
    id: passwordFieldRoot

    property alias text: passwordInput.text
    property string placeholder: "Enter Password..."
    property color textColor: "#cdd6f4"
    property color placeholderColor: "#a6adc8"
    property color accentColor: "#cba6f7"
    property color errorColor: "#f38ba8"
    property color bgBaseColor: "#1e1e2e"
    property color bgFocusColor: "#313244"
    property bool isLoggingIn: false
    property bool hasError: false
    property bool isPasswordHidden: true

    signal submitted()

    implicitWidth: 320
    implicitHeight: 52

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
        radius: 26
        color: passwordInput.activeFocus ? passwordFieldRoot.bgFocusColor : passwordFieldRoot.bgBaseColor
        border.color: passwordFieldRoot.hasError ? passwordFieldRoot.errorColor
                                                 : (passwordInput.activeFocus ? passwordFieldRoot.accentColor : "#313244")
        border.width: passwordInput.activeFocus || passwordFieldRoot.hasError ? 2 : 1

        Behavior on color { ColorAnimation { duration: 150 } }
        Behavior on border.color { ColorAnimation { duration: 150 } }

        Row {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 12
            spacing: 10

            // Lock Icon
            Image {
                id: lockIcon
                width: 18
                height: 18
                source: "../assets/icons/lock.svg"
                fillMode: Image.PreserveAspectFit
                anchors.verticalCenter: parent.verticalCenter
                opacity: passwordInput.activeFocus ? 1.0 : 0.6
            }

            // Input Box
            TextInput {
                id: passwordInput
                width: parent.width - lockIcon.width - eyeToggle.width - submitBtn.width - 36
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
                    opacity: 0.7
                }
            }

            // Reveal/Hide Password Button
            Item {
                id: eyeToggle
                width: 28
                height: 28
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

            // Submit Button
            Rectangle {
                id: submitBtn
                width: 32
                height: 32
                radius: 16
                anchors.verticalCenter: parent.verticalCenter
                color: submitMouseArea.containsMouse ? "#b4befe" : passwordFieldRoot.accentColor
                opacity: (passwordInput.text.length > 0 && !passwordFieldRoot.isLoggingIn) ? 1.0 : 0.35

                Behavior on color { ColorAnimation { duration: 150 } }
                Behavior on opacity { NumberAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "➔"
                    color: "#11111b"
                    font.pixelSize: 14
                    font.bold: true
                }

                MouseArea {
                    id: submitMouseArea
                    anchors.fill: parent
                    cursorShape: (passwordInput.text.length > 0 && !passwordFieldRoot.isLoggingIn) ? Qt.PointingHandCursor : Qt.ArrowCursor
                    hoverEnabled: true
                    onClicked: {
                        if (passwordInput.text.length > 0 && !passwordFieldRoot.isLoggingIn) {
                            passwordFieldRoot.submitted()
                        }
                    }
                }
            }
        }
    }
}
