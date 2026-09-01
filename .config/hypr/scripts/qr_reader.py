#!/usr/bin/env python3
"""
Hyprland Screen QR Code Scanner & Reader Utility
Select any region on screen (or capture full screen/window), decode QR / 2D barcodes,
copy decoded text to Wayland clipboard, and show an interactive notification.
"""

import sys
import shutil
import argparse
import subprocess
import html
import io
from pathlib import Path

# Slurp styling matching Hyprland Catppuccin theme
SLURP_ARGS = ["-b", "00000044", "-c", "cba6f7ee", "-s", "00000000", "-w", "2"]

def notify(title, body, icon="qr-code", actions=None, timeout=6000):
    """Send desktop notification with optional actions."""
    if not shutil.which("notify-send"):
        return
    cmd = [
        "notify-send",
        "-a", "QR Code Reader",
        "-i", str(icon),
        "-t", str(timeout),
    ]
    if actions:
        for act_id, act_label in actions:
            cmd.append(f"--action={act_id}={act_label}")
    cmd.extend([title, body])

    try:
        if actions:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
            out, _ = proc.communicate()
            return out.strip()
        else:
            subprocess.Popen(cmd)
    except Exception:
        pass
    return None

def copy_to_clipboard(text: str):
    """Copy text to Wayland clipboard (wl-copy) or fallback."""
    if shutil.which("wl-copy"):
        p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=text)
        return True
    elif shutil.which("xclip"):
        p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=text)
        return True
    return False

def get_active_window_geometry():
    """Get active window geometry from hyprctl."""
    if not shutil.which("hyprctl"):
        return None
    try:
        import json
        res = subprocess.run(["hyprctl", "-j", "activewindow"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            at = data.get("at", [0, 0])
            size = data.get("size", [0, 0])
            if size[0] > 0 and size[1] > 0:
                return f"{at[0]},{at[1]} {size[0]}x{size[1]}"
    except Exception:
        pass
    return None

def capture_image_bytes(mode="area", custom_geom=None):
    """Capture screen area or window and return image bytes (PNG)."""
    if not shutil.which("grim"):
        notify("❌ Error", "grim is not installed.\nRun: sudo pacman -S grim", "dialog-error")
        return None

    if mode == "area":
        if not shutil.which("slurp"):
            notify("❌ Error", "slurp is not installed.\nRun: sudo pacman -S slurp", "dialog-error")
            return None
        res = subprocess.run(["slurp"] + SLURP_ARGS, capture_output=True, text=True)
        if res.returncode != 0 or not res.stdout.strip():
            # User cancelled selection
            return None
        geometry = res.stdout.strip()
        cmd = ["grim", "-g", geometry, "-"]
    elif mode == "window":
        geom = custom_geom or get_active_window_geometry()
        if not geom:
            notify("❌ Error", "Could not detect active window geometry.", "dialog-error")
            return None
        cmd = ["grim", "-g", geom, "-"]
    elif mode == "full":
        cmd = ["grim", "-"]
    elif mode == "clipboard":
        if shutil.which("wl-paste"):
            res = subprocess.run(["wl-paste", "--type", "image/png"], capture_output=True)
            if res.returncode == 0 and res.stdout:
                return res.stdout
        notify("⚠️ Clipboard", "No PNG image found in clipboard.", "dialog-warning")
        return None
    else:
        cmd = ["grim", "-"]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, _ = p.communicate()
    if p.returncode == 0 and stdout_data:
        return stdout_data
    return None

def decode_qr(image_bytes: bytes) -> list:
    """
    Decode QR code / barcode from image bytes.
    Tries zbarimg first, then falls back to python libraries if available.
    """
    results = []

    # Method 1: zbarimg CLI
    if shutil.which("zbarimg"):
        try:
            # -q: quiet, --raw: raw data only
            p = subprocess.Popen(
                ["zbarimg", "-q", "--raw", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            out, _ = p.communicate(input=image_bytes)
            if p.returncode == 0 and out:
                # Can contain multiple lines if multiple codes detected
                decoded = out.decode("utf-8", errors="replace").strip()
                if decoded:
                    results.append(decoded)
                    return results
        except Exception:
            pass

    # Method 2: pyzbar Python module
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        decoded_objs = pyzbar_decode(img)
        for obj in decoded_objs:
            data = obj.data.decode("utf-8", errors="replace")
            if data and data not in results:
                results.append(data)
        if results:
            return results
    except ImportError:
        pass
    except Exception:
        pass

    # Method 3: cv2 / OpenCV QRCodeDetector
    try:
        import cv2
        import numpy as np
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        if data and data.strip():
            results.append(data.strip())
            return results
    except ImportError:
        pass
    except Exception:
        pass

    return results

def is_url(text: str) -> bool:
    """Check if string is an HTTP/HTTPS URL."""
    s = text.strip()
    return s.startswith("http://") or s.startswith("https://") or s.startswith("www.")

def open_url(url: str):
    """Open URL with xdg-open or default browser."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    if shutil.which("xdg-open"):
        subprocess.Popen(["xdg-open", url])

def main():
    parser = argparse.ArgumentParser(description="Read and decode QR code from screen area, window, or clipboard.")
    parser.add_argument("-a", "--area", action="store_true", default=True, help="Select a screen region with cursor (default)")
    parser.add_argument("-f", "--full", action="store_true", help="Capture full screen")
    parser.add_argument("-w", "--window", action="store_true", help="Capture active window")
    parser.add_argument("-c", "--clipboard", action="store_true", help="Read QR from image currently in clipboard")
    parser.add_argument("-i", "--image", type=str, help="Read QR from a local image file")
    parser.add_argument("-o", "--open", action="store_true", help="Automatically open URL in browser if decoded text is a URL")
    parser.add_argument("--raw", action="store_true", help="Print only raw decoded content to stdout without notification")

    args = parser.parse_args()

    # Determine mode
    mode = "area"
    if args.clipboard:
        mode = "clipboard"
    elif args.window:
        mode = "window"
    elif args.full:
        mode = "full"

    image_bytes = None
    if args.image:
        img_path = Path(args.image).expanduser()
        if not img_path.exists():
            print(f"Error: File {img_path} not found.", file=sys.stderr)
            sys.exit(1)
        image_bytes = img_path.read_bytes()
    else:
        # Check decoder dependency before capturing
        has_decoder = (
            shutil.which("zbarimg") is not None
            or shutil.which("zbar") is not None
        )
        if not has_decoder:
            try:
                import pyzbar  # noqa: F401
                has_decoder = True
            except ImportError:
                try:
                    import cv2  # noqa: F401
                    has_decoder = True
                except ImportError:
                    pass

        if not has_decoder:
            notify(
                "❌ QR Decoder Missing",
                "Please install <b>zbar</b> to enable QR decoding:\n<code>sudo pacman -S zbar</code>",
                icon="dialog-error",
                timeout=8000
            )
            print("Error: No QR decoder found. Install zbar: sudo pacman -S zbar", file=sys.stderr)
            sys.exit(1)

        image_bytes = capture_image_bytes(mode=mode)

    if not image_bytes:
        sys.exit(0)  # Selection cancelled or no image

    decoded_list = decode_qr(image_bytes)

    if not decoded_list:
        if not args.raw:
            notify("⚠️ QR Reader", "No QR code or barcode detected in the selected area.", "dialog-warning")
        print("No QR code detected.", file=sys.stderr)
        sys.exit(2)

    result_text = "\n".join(decoded_list)

    # Print to stdout
    print(result_text)

    # Copy to clipboard
    copy_to_clipboard(result_text)

    if args.raw:
        sys.exit(0)

    # Format notification preview
    preview = result_text if len(result_text) <= 160 else result_text[:160] + "..."
    escaped_preview = html.escape(preview)

    actions = [("copy", "📋 Copy")]
    is_link = is_url(result_text)
    if is_link:
        actions.append(("open", "🌐 Open Link"))

    selected_action = notify(
        "📱 QR Code Decoded & Copied",
        f"<b>Content:</b>\n<i>{escaped_preview}</i>",
        icon="edit-copy",
        actions=actions,
        timeout=6000
    )

    if args.open and is_link:
        open_url(result_text)
    elif selected_action == "open" and is_link:
        open_url(result_text)

if __name__ == "__main__":
    main()
