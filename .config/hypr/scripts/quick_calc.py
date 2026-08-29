#!/usr/bin/env python3
"""
Hyprland Quick Calculator (Fuzzel / Wofi Integration)
Evaluates math expressions with Python's math module and copies results to clipboard.
"""

import sys
import math
import shutil
import subprocess

# Safe mathematical environment
SAFE_MATH = {
    k: v for k, v in math.__dict__.items() if not k.startswith("__")
}
SAFE_MATH.update({
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
})

def evaluate_expression(expr: str) -> str:
    expr = expr.strip()
    if not expr:
        return ""
    # Normalize common operators
    expr_clean = expr.replace("x", "*").replace("X", "*").replace("^", "**").replace("÷", "/")
    try:
        res = eval(expr_clean, {"__builtins__": {}}, SAFE_MATH)
        if isinstance(res, float):
            # Format nicely
            if res.is_integer():
                return str(int(res))
            return f"{res:.6g}"
        return str(res)
    except Exception as e:
        return f"Error: {e}"

def main():
    prompt = "Calc (=): "
    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", prompt, "--width", "36", "--lines", "6"]
    elif shutil.which("wofi"):
        cmd = ["wofi", "--dmenu", "--prompt", prompt, "--width", "380", "--height", "220", "--insensitive"]
    else:
        sys.exit(1)

    initial_choices = [
        "Enter math expression (e.g. 1500 * 1.18)",
        "sqrt(256) + 2**8",
        "round(sin(pi/4), 4)",
        "hex(255) or 0xFF + 1",
    ]
    input_str = "\n".join(initial_choices)

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out, _ = proc.communicate(input=input_str)
    query = out.strip()

    if not query or query.startswith("Enter math") or query.startswith("sqrt") or query.startswith("round") or query.startswith("hex"):
        return

    result = evaluate_expression(query)
    if not result or result.startswith("Error:"):
        if shutil.which("notify-send"):
            subprocess.Popen([
                "notify-send",
                "-a", "Calculator",
                "-i", "calc",
                "-t", "3000",
                "⚠️ Calculation Error",
                f"Could not evaluate: <code>{query}</code>"
            ])
        return

    # Copy to clipboard
    if shutil.which("wl-copy"):
        p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=result)

    if shutil.which("notify-send"):
        subprocess.Popen([
            "notify-send",
            "-a", "Calculator",
            "-i", "accessories-calculator",
            "-t", "4000",
            f"🧮 Result: {result}",
            f"<code>{query}</code> = <b>{result}</b>\n(Copied to clipboard)"
        ])

if __name__ == "__main__":
    main()
