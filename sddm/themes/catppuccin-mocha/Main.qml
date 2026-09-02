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
    property string bgSource: (typeof config !== "undefined" && config.Background) ? config.Background : "assets/background.jpg"
    property string fontName: (typeof config !== "undefined" && config.FontFamily) ? config.FontFamily : "JetBrainsMono Nerd Font"
    property string clockFmt: (typeof config !== "undefined" && config.ClockFormat) ? config.ClockFormat : "HH:mm"
    property string dateFmt: (typeof config !== "undefined" && config.DateFormat) ? config.DateFormat : "dddd, d 'of' MMMM"
    property string placeholder: (typeof config !== "undefined" && config.PlaceholderText) ? config.PlaceholderText : "Password"
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
    property bool showSessionDropdown: false

    // Initialize User Data
    function findUserIndex(username) {
        if (typeof userModel !== "undefined" && userModel.count > 0) {
            for (var i = 0; i < userModel.count; i++) {
                var u = userModel.data(userModel.index(i, 0), Qt.UserRole + 1) || userModel.data(userModel.index(i, 0), Qt.DisplayRole) || ""
                if (u === username) return i
            }
        }
        return 0
    }

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
        if (usernameBox) {
            usernameBox.text = selectedUserName
        }
    }

    Component.onCompleted: {
        var defaultIdx = 0
        if (typeof userModel !== "undefined" && userModel.lastUser) {
            defaultIdx = findUserIndex(userModel.lastUser)
        } else if (typeof userModel !== "undefined" && userModel.lastIndex >= 0) {
            defaultIdx = userModel.lastIndex
        }
        updateSelectedUser(defaultIdx)
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
        var user = usernameBox.text.trim() || root.selectedUserName
        if (passwordBox.text.length === 0 || root.isLoggingIn) return
        root.isLoggingIn = true
        root.errorMessage = ""
        passwordBox.hasError = false

        if (typeof sddm !== "undefined") {
            sddm.login(user, passwordBox.text, root.currentSessionIdx)
        } else {
            console.log("SDDM Test Login: User=" + user + ", Session=" + root.currentSessionIdx)
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

    // 1. Wallpaper Background (Full Screen)
    Image {
        id: bgImage
        anchors.fill: parent
        source: root.bgSource
        fillMode: Image.PreserveAspectCrop
        smooth: true
        asynchronous: true
        onStatusChanged: {
            if (status === Image.Error && source !== "assets/background.jpg") {
                source = "assets/background.jpg"
            }
        }
    }

    // 2. Left Frosted Glass Sidebar Panel
    Rectangle {
        id: leftPanel
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: Math.max(420, Math.min(520, root.width * 0.36))
        color: Qt.rgba(20/255, 22/255, 33/255, 0.82)

        // Right subtle border dividing sidebar from artwork
        Rectangle {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 1
            color: Qt.rgba(255/255, 255/255, 255/255, 0.12)
        }

        // Close / Preview hint indicator at top-left
        Row {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.margins: 16
            spacing: 8
            opacity: 0.65

            Text {
                text: "✕ " + root.hostText
                color: "#a6adc8"
                font.family: root.fontName
                font.pixelSize: 11
            }
        }

        // Main Left Content Column
        Column {
            id: mainColumn
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: -30
            width: 320
            spacing: 16

            // Clock & Greeting
            ClockWidget {
                id: clockSection
                anchors.horizontalCenter: parent.horizontalCenter
                greetingText: "Welcome!"
                timeFormat: root.clockFmt
                dateFormat: root.dateFmt
                fontFamily: root.fontName
            }

            Item {
                width: 1
                height: 12
            }

            // Username Input Pill with Badge
            UsernameField {
                id: usernameBox
                anchors.horizontalCenter: parent.horizontalCenter
                isMultipleUsers: (typeof userModel !== "undefined" && userModel.count > 1)
                text: root.selectedUserName
                onUserSelectClicked: {
                    root.showUserDropdown = !root.showUserDropdown
                }
                onSubmitted: {
                    passwordBox.focusInput()
                }
            }

            // User Selection Dropdown List
            Rectangle {
                id: userSelectList
                visible: root.showUserDropdown && (typeof userModel !== "undefined" && userModel.count > 1)
                anchors.horizontalCenter: parent.horizontalCenter
                width: 320
                height: Math.min(150, (typeof userModel !== "undefined" ? userModel.count * 36 : 36) + 8)
                radius: 14
                color: "#11111b"
                border.color: "#cba6f7"
                border.width: 1
                clip: true
                z: 100

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

            // Password Input Pill
            PasswordField {
                id: passwordBox
                anchors.horizontalCenter: parent.horizontalCenter
                placeholder: root.placeholder
                isLoggingIn: root.isLoggingIn
                onSubmitted: root.doLogin()
            }

            // Show Password Checkbox
            Item {
                width: parent.width
                height: 24

                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 8

                    Rectangle {
                        width: 15
                        height: 15
                        radius: 3
                        color: !passwordBox.isPasswordHidden ? "#cba6f7" : Qt.rgba(255/255, 255/255, 255/255, 0.1)
                        border.color: !passwordBox.isPasswordHidden ? "#cba6f7" : Qt.rgba(255/255, 255/255, 255/255, 0.4)
                        border.width: 1
                        anchors.verticalCenter: parent.verticalCenter

                        Text {
                            anchors.centerIn: parent
                            text: "✓"
                            visible: !passwordBox.isPasswordHidden
                            color: "#11111b"
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }

                    Text {
                        text: "Show Password"
                        color: "#a6adc8"
                        font.family: root.fontName
                        font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    hoverEnabled: true
                    onClicked: {
                        passwordBox.isPasswordHidden = !passwordBox.isPasswordHidden
                    }
                }
            }

            // Caps Lock Warning
            Rectangle {
                id: capsWarning
                visible: (typeof keyboard !== "undefined" && keyboard.capsLock)
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                height: 28
                radius: 14
                color: Qt.rgba(250/255, 179/255, 135/255, 0.18)
                border.color: "#fab387"
                border.width: 1

                Row {
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

            // Error Message Banner
            Rectangle {
                id: errorBox
                visible: root.errorMessage.length > 0
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                height: 30
                radius: 10
                color: Qt.rgba(243/255, 139/255, 168/255, 0.15)
                border.color: "#f38ba8"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: root.errorMessage
                    color: "#f38ba8"
                    font.family: root.fontName
                    font.pixelSize: 11
                    font.bold: true
                }
            }

            Item {
                width: 1
                height: 8
            }

            // Solid Pill "Log in" Button
            Rectangle {
                id: loginButton
                width: 320
                height: 44
                radius: 22
                anchors.horizontalCenter: parent.horizontalCenter
                color: loginMouse.pressed ? "#b4befe" : (loginMouse.containsMouse ? "#e0def4" : "#ffffff")
                opacity: root.isLoggingIn ? 0.7 : 1.0

                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: root.isLoggingIn ? "Logging in..." : "Log in"
                    color: "#1e1e2e"
                    font.family: root.fontName
                    font.pixelSize: 14
                    font.bold: true
                }

                MouseArea {
                    id: loginMouse
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    hoverEnabled: true
                    onClicked: {
                        root.doLogin()
                    }
                }
            }

            // Session Indicator / Selector
            Item {
                id: sessionBox
                width: 320
                height: 28
                anchors.horizontalCenter: parent.horizontalCenter

                Row {
                    anchors.centerIn: parent
                    spacing: 6

                    Text {
                        text: "Session: " + ((typeof sessionModel !== "undefined" && sessionModel.count > 0 && root.currentSessionIdx >= 0 && root.currentSessionIdx < sessionModel.count) ? (sessionModel.data(sessionModel.index(root.currentSessionIdx, 0), Qt.UserRole + 2) || sessionModel.data(sessionModel.index(root.currentSessionIdx, 0), Qt.DisplayRole) || "Hyprland") : "Hyprland")
                        color: sessionMouse.containsMouse ? "#ffffff" : "#a6adc8"
                        font.family: root.fontName
                        font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                        Behavior on color { ColorAnimation { duration: 150 } }
                    }

                    Image {
                        width: 10
                        height: 10
                        source: "assets/icons/chevron-down.svg"
                        fillMode: Image.PreserveAspectFit
                        anchors.verticalCenter: parent.verticalCenter
                        opacity: sessionMouse.containsMouse ? 1.0 : 0.6
                    }
                }

                MouseArea {
                    id: sessionMouse
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    hoverEnabled: true
                    onClicked: {
                        root.showSessionDropdown = !root.showSessionDropdown
                    }
                }
            }

            // Session Selection Dropdown List
            Rectangle {
                id: sessionSelectList
                visible: root.showSessionDropdown && (typeof sessionModel !== "undefined" && sessionModel.count > 1)
                anchors.horizontalCenter: parent.horizontalCenter
                width: 260
                height: Math.min(160, (typeof sessionModel !== "undefined" ? sessionModel.count * 34 : 34) + 8)
                radius: 12
                color: "#11111b"
                border.color: "#cba6f7"
                border.width: 1
                clip: true
                z: 100

                ListView {
                    anchors.fill: parent
                    anchors.margins: 4
                    model: (typeof sessionModel !== "undefined") ? sessionModel : null
                    spacing: 2

                    delegate: Rectangle {
                        width: parent.width
                        height: 30
                        radius: 6
                        color: sMouse.containsMouse ? "#313244" : (index === root.currentSessionIdx ? Qt.rgba(203/255, 166/255, 247/255, 0.2) : "transparent")

                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            spacing: 8

                            Image {
                                width: 12
                                height: 12
                                source: "assets/icons/session.svg"
                                fillMode: Image.PreserveAspectFit
                                anchors.verticalCenter: parent.verticalCenter
                            }

                            Text {
                                text: model.name || model.display || "Session"
                                color: "#cdd6f4"
                                font.family: root.fontName
                                font.pixelSize: 12
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }

                        MouseArea {
                            id: sMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                root.currentSessionIdx = index
                                root.showSessionDropdown = false
                            }
                        }
                    }
                }
            }
        }

        // 3. Bottom Power Action Controls
        PowerMenu {
            id: bottomPowerMenu
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 36
            anchors.horizontalCenter: parent.horizontalCenter
            fontFamily: root.fontName

            onPowerOffClicked: {
                confirmDialog.title = "Shut Down System?"
                confirmDialog.message = "Are you sure you want to turn off this device?"
                confirmDialog.confirmText = "Shut Down"
                confirmDialog.accentColor = "#f38ba8"
                confirmDialog.confirmed.connect(function() {
                    if (typeof sddm !== "undefined") sddm.powerOff()
                })
                confirmDialog.open()
            }
            onRebootClicked: {
                confirmDialog.title = "Restart System?"
                confirmDialog.message = "Are you sure you want to restart your device?"
                confirmDialog.confirmText = "Restart"
                confirmDialog.accentColor = "#fab387"
                confirmDialog.confirmed.connect(function() {
                    if (typeof sddm !== "undefined") sddm.reboot()
                })
                confirmDialog.open()
            }
            onSuspendClicked: {
                if (typeof sddm !== "undefined") sddm.suspend()
            }
        }
    }

    // Confirmation Dialog
    ConfirmDialog {
        id: confirmDialog
        z: 1000
    }

    // Global Key Handlers
    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Escape) {
            root.showUserDropdown = false
            root.showSessionDropdown = false
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
