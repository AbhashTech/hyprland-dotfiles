import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#1e1e2e"

    // Configuration / Fallback Values
    property string bgSource: (typeof config !== "undefined" && config.Background) ? config.Background : "assets/background.svg"
    property string fontName: (typeof config !== "undefined" && config.FontFamily) ? config.FontFamily : "JetBrainsMono Nerd Font"
    property string clockFmt: (typeof config !== "undefined" && config.ClockFormat) ? config.ClockFormat : "HH:mm"
    property string dateFmt: (typeof config !== "undefined" && config.DateFormat) ? config.DateFormat : "dddd, MMMM d, yyyy"
    property string placeholder: (typeof config !== "undefined" && config.PlaceholderText) ? config.PlaceholderText : "Enter Password..."
    property string hostText: (typeof sddm !== "undefined" && sddm.hostName) ? sddm.hostName : "hyprland-os"

    // State Variables
    property int currentSessionIdx: (typeof sessionModel !== "undefined" && sessionModel.lastIndex >= 0) ? sessionModel.lastIndex : 0
    property int currentUserIdx: (typeof userModel !== "undefined" && userModel.lastIndex >= 0) ? userModel.lastIndex : 0
    property string selectedUserName: ""
    property string selectedRealName: ""
    property string selectedAvatarPath: ""
    property bool isLoggingIn: false
    property string errorMessage: ""
    property bool showUserDropdown: false

    // Initialize User Data
    function updateSelectedUser(idx) {
        if (typeof userModel !== "undefined" && userModel.count > 0) {
            if (idx < 0 || idx >= userModel.count) idx = 0
            currentUserIdx = idx
            selectedUserName = userModel.data(userModel.index(idx, 0), Qt.UserRole + 1) || userModel.data(userModel.index(idx, 0), Qt.DisplayRole) || ""
            selectedRealName = userModel.data(userModel.index(idx, 0), Qt.UserRole + 2) || ""
            selectedAvatarPath = userModel.data(userModel.index(idx, 0), Qt.UserRole + 4) || ""
        } else {
            selectedUserName = "kunal"
            selectedRealName = "Kunal"
            selectedAvatarPath = ""
        }
    }

    Component.onCompleted: {
        updateSelectedUser(currentUserIdx)
        passwordBox.focusInput()
    }

    // SDDM Signal Connections
    Connections {
        target: (typeof sddm !== "undefined") ? sddm : null
        ignoreUnknownSignals: true

        function onLoginSucceeded() {
            root.errorMessage = ""
            root.isLoggingIn = false
        }

        function onLoginFailed() {
            root.errorMessage = "Authentication failed. Please try again."
            root.isLoggingIn = false
            passwordBox.text = ""
            passwordBox.hasError = true
            passwordBox.triggerShake()
            passwordBox.focusInput()
        }

        function onInformationMessage(message) {
            root.errorMessage = message
            root.isLoggingIn = false
        }
    }

    // Submit Login Function
    function doLogin() {
        if (passwordBox.text.length === 0 || root.isLoggingIn) return
        root.isLoggingIn = true
        root.errorMessage = ""
        passwordBox.hasError = false

        if (typeof sddm !== "undefined") {
            sddm.login(root.selectedUserName, passwordBox.text, root.currentSessionIdx)
        } else {
            console.log("SDDM Test Login: User=" + root.selectedUserName + ", Session=" + root.currentSessionIdx)
            // Test Mode Simulation: reset after 1.5s
            testTimer.restart()
        }
    }

    Timer {
        id: testTimer
        interval: 1200
        onTriggered: {
            root.isLoggingIn = false
            passwordBox.focusInput()
        }
    }

    // 1. Wallpaper Background
    Image {
        id: bgImage
        anchors.fill: parent
        source: root.bgSource
        fillMode: Image.PreserveAspectCrop
        smooth: true
        asynchronous: true
        onStatusChanged: {
            if (status === Image.Error && source !== "assets/background.svg") {
                source = "assets/background.svg"
            }
        }
    }

    // Subtle dark gradient vignette
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(17/255, 17/255, 27/255, 0.35)
    }

    // 2. Top Status Bar Header
    StatusHeader {
        id: statusHeader
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: 16
        hostName: root.hostText
        sessionModel: (typeof sessionModel !== "undefined") ? sessionModel : null
        currentSessionIndex: root.currentSessionIdx
        showSessions: (typeof config === "undefined" || config.ShowSessions !== "false")
        showPower: (typeof config === "undefined" || config.ShowPowerButtons !== "false")

        onSessionChanged: function(idx) {
            root.currentSessionIdx = idx
        }
        onPowerOff: {
            confirmDialog.title = "Shut Down System?"
            confirmDialog.message = "Are you sure you want to turn off this device?"
            confirmDialog.confirmText = "Shut Down"
            confirmDialog.accentColor = "#f38ba8"
            confirmDialog.confirmed.connect(function() {
                if (typeof sddm !== "undefined") sddm.powerOff()
            })
            confirmDialog.open()
        }
        onReboot: {
            confirmDialog.title = "Restart System?"
            confirmDialog.message = "Are you sure you want to restart your device?"
            confirmDialog.confirmText = "Restart"
            confirmDialog.accentColor = "#fab387"
            confirmDialog.confirmed.connect(function() {
                if (typeof sddm !== "undefined") sddm.reboot()
            })
            confirmDialog.open()
        }
        onSuspend: {
            if (typeof sddm !== "undefined") sddm.suspend()
        }
        onHibernate: {
            if (typeof sddm !== "undefined") sddm.hibernate()
        }
    }

    // 3. Central Login Container
    Item {
        id: centerArea
        anchors.centerIn: parent
        width: 440
        height: mainCard.height + clockSection.height + 24

        Column {
            anchors.centerIn: parent
            spacing: 20
            width: parent.width

            // Clock & Dynamic Greeting
            ClockWidget {
                id: clockSection
                anchors.horizontalCenter: parent.horizontalCenter
                timeFormat: root.clockFmt
                dateFormat: root.dateFmt
                fontFamily: root.fontName
                currentUserName: root.selectedRealName !== "" ? root.selectedRealName : root.selectedUserName
            }

            // Glassmorphic Login Card
            GlassCard {
                id: mainCard
                width: parent.width
                height: cardContent.implicitHeight + 56
                cardRadius: 24
                cardColor: Qt.rgba(24/255, 24/255, 37/255, 0.78)
                borderColor: passwordBox.hasError ? "#f38ba8" : Qt.rgba(203/255, 166/255, 247/255, 0.25)
                borderWidth: 1.5

                Column {
                    id: cardContent
                    anchors.centerIn: parent
                    spacing: 16
                    width: parent.width - 48

                    // User Profile Avatar & Switcher
                    UserAvatar {
                        id: avatarComponent
                        anchors.horizontalCenter: parent.horizontalCenter
                        avatarSource: root.selectedAvatarPath
                        username: root.selectedUserName
                        realName: root.selectedRealName
                        isMultipleUsers: (typeof userModel !== "undefined" && userModel.count > 1)
                        onUserClicked: {
                            root.showUserDropdown = !root.showUserDropdown
                        }
                    }

                    // User Selection Dropdown List (if multiple users)
                    Rectangle {
                        id: userSelectList
                        visible: root.showUserDropdown && (typeof userModel !== "undefined" && userModel.count > 1)
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 280
                        height: Math.min(150, (typeof userModel !== "undefined" ? userModel.count * 36 : 36) + 8)
                        radius: 12
                        color: "#11111b"
                        border.color: "#cba6f7"
                        border.width: 1
                        clip: true

                        ListView {
                            anchors.fill: parent
                            anchors.margins: 4
                            model: (typeof userModel !== "undefined") ? userModel : null
                            spacing: 2

                            delegate: Rectangle {
                                width: parent.width
                                height: 32
                                radius: 8
                                color: userMouse.containsMouse ? "#313244" : (index === root.currentUserIdx ? Qt.rgba(203/255, 166/255, 247/255, 0.2) : "transparent")

                                Row {
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    spacing: 8

                                    Image {
                                        width: 14
                                        height: 14
                                        source: "assets/icons/user.svg"
                                        fillMode: Image.PreserveAspectFit
                                        anchors.verticalCenter: parent.verticalCenter
                                    }

                                    Text {
                                        text: model.realName || model.name || "User"
                                        color: "#cdd6f4"
                                        font.family: root.fontName
                                        font.pixelSize: 12
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }

                                MouseArea {
                                    id: userMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        root.updateSelectedUser(index)
                                        root.showUserDropdown = false
                                        passwordBox.focusInput()
                                    }
                                }
                            }
                        }
                    }

                    // Caps Lock Indicator
                    Rectangle {
                        id: capsWarning
                        visible: (typeof keyboard !== "undefined" && keyboard.capsLock)
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: capsRow.implicitWidth + 20
                        height: 26
                        radius: 13
                        color: Qt.rgba(250/255, 179/255, 135/255, 0.18)
                        border.color: "#fab387"
                        border.width: 1

                        Row {
                            id: capsRow
                            anchors.centerIn: parent
                            spacing: 6

                            Image {
                                width: 12
                                height: 12
                                source: "assets/icons/warning.svg"
                                fillMode: Image.PreserveAspectFit
                                anchors.verticalCenter: parent.verticalCenter
                            }

                            Text {
                                text: "Caps Lock is ON"
                                color: "#fab387"
                                font.family: root.fontName
                                font.pixelSize: 11
                                font.bold: true
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }

                    // Password Input Pill
                    PasswordField {
                        id: passwordBox
                        anchors.horizontalCenter: parent.horizontalCenter
                        placeholder: root.placeholder
                        isLoggingIn: root.isLoggingIn
                        onSubmitted: root.doLogin()
                    }

                    // Error Message Banner
                    Rectangle {
                        id: errorBox
                        visible: root.errorMessage.length > 0
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: Math.min(parent.width, errorLabel.implicitWidth + 24)
                        height: 30
                        radius: 8
                        color: Qt.rgba(243/255, 139/255, 168/255, 0.15)
                        border.color: "#f38ba8"
                        border.width: 1

                        Text {
                            id: errorLabel
                            anchors.centerIn: parent
                            text: root.errorMessage
                            color: "#f38ba8"
                            font.family: root.fontName
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }
                }
            }
        }
    }

    // 4. Bottom Footer Hint
    Row {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 8
        opacity: 0.65

        Text {
            text: "Press [Enter] to login • [Tab] to navigate"
            color: "#a6adc8"
            font.family: root.fontName
            font.pixelSize: 12
        }
    }

    // 5. Modal Confirmation Dialog (Shutdown/Reboot)
    ConfirmDialog {
        id: confirmDialog
        z: 1000
    }

    // Global Key Handlers
    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Escape) {
            root.showUserDropdown = false
            confirmDialog.close()
            event.accepted = true
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            if (!confirmDialog.visible && !root.isLoggingIn) {
                root.doLogin()
                event.accepted = true
            }
        }
    }
}
