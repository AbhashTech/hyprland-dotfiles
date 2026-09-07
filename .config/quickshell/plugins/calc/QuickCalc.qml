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

    function fact(n) {
        n = Math.round(n);
        if (n < 0 || n > 170) return NaN;
        if (n === 0 || n === 1) return 1;
        var r = 1;
        for (var i = 2; i <= n; i++) r *= i;
        return r;
    }

    function formatNumber(num) {
        if (typeof num !== "number" || isNaN(num)) return null;
        if (!isFinite(num)) return num > 0 ? "Infinity" : "-Infinity";

        // Snap values extremely close to 0 (e.g. sin(pi)) to 0
        if (Math.abs(num) < 1e-14) return "0";

        // Eliminate IEEE 754 precision artifacts (e.g. 0.30000000000000004 -> 0.3)
        var rounded = parseFloat(num.toPrecision(12));

        // Snap numbers very close to integers (e.g. 1.4 / 0.1 -> 14)
        if (Math.abs(rounded - Math.round(rounded)) < 1e-10) {
            rounded = Math.round(rounded);
        }

        return String(rounded);
    }

    function cleanExpression(expr) {
        var s = expr.trim();
        // Remove leading '=' signs e.g. "= 0.2+0.1"
        s = s.replace(/^=+\s*/, "");
        if (!s) return "";

        // Remove currency symbols
        s = s.replace(/[\$\€\£\¥\₹]/g, "");

        // Unicode math symbols
        s = s.replace(/×/g, "*")
             .replace(/÷/g, "/")
             .replace(/−/g, "-")
             .replace(/⁄/g, "/")
             .replace(/∕/g, "/");

        // Remove thousands separators: e.g. 1,000 or 12,345,678
        s = s.replace(/(\d),(\d{3})(?!\d)/g, "$1$2");

        // Exponentiation ^ -> **
        s = s.replace(/\^/g, "**");

        // Factorial: 5! -> fact(5) or (3+2)! -> fact(3+2)
        s = s.replace(/(\d+)!/g, "fact($1)");
        s = s.replace(/\(([^()]+)\)!/g, "fact($1)");

        // Percentages:
        // A + B% -> A + (A * (B / 100))
        // A - B% -> A - (A * (B / 100))
        s = s.replace(/(\d+(?:\.\d+)?)\s*([\+\-])\s*(\d+(?:\.\d+)?)\s*%/g, function(_, a, op, b) {
            return a + " " + op + " (" + a + " * (" + b + " / 100))";
        });
        // Remaining N% -> (N / 100)
        s = s.replace(/(\d+(?:\.\d+)?)\s*%/g, "($1 / 100)");

        // Multiplication letter x/X (only when acting as multiplication operator, avoiding exp, max, hex 0x...)
        s = s.replace(/(\d|\))\s*[xX]\s*(\d|\(|\b(?:pi|PI|e|E|sin|cos|tan|sqrt|abs|ln|log|cbrt)\b)/g, "$1 * $2");
        s = s.replace(/(\b\d+)\s*[xX]\s*(\b\d+)/g, "$1 * $2");

        // Implicit multiplication:
        // (number)(...) -> number * (...)
        s = s.replace(/(^|[^a-zA-Z0-9_])(\d+(?:\.\d+)?)\s*\(/g, "$1$2 * (");
        // (...)(...) -> (...) * (...)
        s = s.replace(/\)\s*\(/g, ") * (");
        // (...)number -> (...) * number
        s = s.replace(/\)\s*(\d)/g, ") * $1");
        // number followed by constant / identifier (e.g. 2pi, 3sqrt, but not 1e5 or 0x10)
        s = s.replace(/(^|[^a-zA-Z0-9_])(\d+(?:\.\d+)?)\s*([a-zA-Z_]\w*)/g, function(match, prefix, num, id, offset, fullStr) {
            var rest = fullStr.slice(offset + prefix.length + num.length);
            if (/^[eE][+-]?\d+/.test(rest)) return match;
            if (num === "0" && /^[xX][0-9a-fA-F]+/.test(rest)) return match;
            return prefix + num + " * " + id;
        });

        return s;
    }

    function balanceParentheses(s) {
        var open = 0;
        for (var i = 0; i < s.length; i++) {
            if (s[i] === '(') open++;
            else if (s[i] === ')') open--;
        }
        while (open > 0) {
            s += ")";
            open--;
        }
        return s;
    }

    function evaluateExpression(expr) {
        root.calculationError = "";
        expr = expr.trim();
        if (!expr) {
            root.calculationResult = "";
            return;
        }

        var clean = cleanExpression(expr);
        if (!clean) {
            root.calculationResult = "";
            return;
        }

        var isIncomplete = /[+\-*/%^,]$/.test(clean);
        var evalClean = balanceParentheses(clean);

        try {
            var factFunc = "function(n) { n = Math.round(n); if (n < 0 || n > 170) return NaN; if (n === 0 || n === 1) return 1; var r = 1; for (var i = 2; i <= n; i++) r *= i; return r; }";
            var scope = "var sin = Math.sin, cos = Math.cos, tan = Math.tan, asin = Math.asin, acos = Math.acos, atan = Math.atan, atan2 = Math.atan2, sinh = Math.sinh, cosh = Math.cosh, tanh = Math.tanh, sqrt = Math.sqrt, cbrt = Math.cbrt, exp = Math.exp, abs = Math.abs, round = Math.round, floor = Math.floor, ceil = Math.ceil, trunc = Math.trunc, sign = Math.sign, min = Math.min, max = Math.max, hypot = Math.hypot, pow = Math.pow, PI = Math.PI, pi = Math.PI, E = Math.E, e = Math.E, log = Math.log, ln = Math.log, log10 = Math.log10, log2 = Math.log2, rad = function(d) { return d * Math.PI / 180; }, deg = function(r) { return r * 180 / Math.PI; }, fact = " + factFunc + ";";
            var res = Function(scope + " return (" + evalClean + ");")();
            if (typeof res === "number") {
                if (isNaN(res)) {
                    if (!isIncomplete) {
                        root.calculationError = "Invalid calculation";
                    }
                    root.calculationResult = "";
                } else if (!isFinite(res)) {
                    root.calculationError = "Cannot divide by zero";
                    root.calculationResult = "";
                } else {
                    root.calculationResult = formatNumber(res);
                }
            } else if (res !== undefined && res !== null) {
                root.calculationResult = String(res);
            }
        } catch (e) {
            if (!isIncomplete) {
                root.calculationError = "Expression error";
            }
            root.calculationResult = "";
        }
    }

    function copyResult() {
        if (root.calculationResult) {
            copyProc.exec(["bash", "-c", "wl-copy -- \"$1\" && (command -v wtype >/dev/null 2>&1 && wtype -M ctrl -k v -m ctrl || true)", "_", root.calculationResult]);
            PluginManager.closeAll();
        }
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
        calcInput.text = "";
        root.calculationResult = "";
        root.calculationError = "";
        calcInput.forceActiveFocus();
    }

    Component.onCompleted: grabFocus()

    Connections {
        target: PluginManager
        function onCalcVisibleChanged() {
            if (PluginManager.calcVisible) {
                root.grabFocus();
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
