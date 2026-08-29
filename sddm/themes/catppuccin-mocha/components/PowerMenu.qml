import QtQuick
import QtQuick.Controls

Item {
    id: powerMenuRoot

    property bool canPowerOff: true
    property bool canReboot: true
    property bool canSuspend: true
    property bool canHibernate: true

    signal powerOffClicked()
    signal rebootClicked()
    signal suspendClicked()
    signal hibernateClicked()

    implicitWidth: powerRow.implicitWidth
    implicitHeight: powerRow.implicitHeight

    Row {
        id: powerRow
        spacing: 10

        // Suspend / Sleep
        ActionButton {
            visible: powerMenuRoot.canSuspend
            iconSource: "../assets/icons/suspend.svg"
            tooltip: "Sleep / Suspend"
            onClicked: powerMenuRoot.suspendClicked()
        }

        // Hibernate
        ActionButton {
            visible: powerMenuRoot.canHibernate
            iconSource: "../assets/icons/hibernate.svg"
            tooltip: "Hibernate"
            onClicked: powerMenuRoot.hibernateClicked()
        }

        // Reboot
        ActionButton {
            visible: powerMenuRoot.canReboot
            iconSource: "../assets/icons/reboot.svg"
            tooltip: "Restart System"
            onClicked: powerMenuRoot.rebootClicked()
        }

        // Power Off / Shutdown
        ActionButton {
            visible: powerMenuRoot.canPowerOff
            iconSource: "../assets/icons/power.svg"
            tooltip: "Shut Down"
            isDestructive: true
            onClicked: powerMenuRoot.powerOffClicked()
        }
    }
}
