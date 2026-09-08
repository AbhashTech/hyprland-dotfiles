#!/usr/bin/env python3
"""
Quickshell File Picker Helper
Handles: directory listing, bookmarks, recents, MIME detection, thumbnails,
         confirm/cancel output for the XDG portal backend.

Commands:
  list <path> [--hidden] [--mime <filter>] [--sort name|size|date] [--desc]
  bookmarks
  add-bookmark <path>
  remove-bookmark <path>
  recents
  add-recent <path>
  confirm <path1> [path2 ...]
  cancel
  request
  mime <path>
"""

import sys
import os
import json
import time
import subprocess
import mimetypes
from pathlib import Path
from datetime import datetime

# Paths
HOME        = os.path.expanduser("~")
CACHE_DIR   = os.path.join(HOME, ".cache", "qs_filepicker")
BOOKMARKS_F = os.path.join(CACHE_DIR, "bookmarks.json")
RECENTS_F   = os.path.join(CACHE_DIR, "recents.json")
THUMB_DIR   = os.path.join(CACHE_DIR, "thumbnails")
RESPONSE_F  = os.path.join(CACHE_DIR, "response.json")
REQUEST_F   = os.path.join(CACHE_DIR, "request.json")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(THUMB_DIR,  exist_ok=True)

# Nerd Font icons keyed by MIME top-type or full MIME
MIME_ICONS = {
    "inode/directory":              "\uf013b",  #  folder
    "image":                        "\uf02e9",  # 
    "video":                        "\uf0177",  # 
    "audio":                        "\uf04d3",  # 
    "text":                         "\uf0219",  # 
    "text/x-python":                "\ue235",   #
    "application/javascript":       "\ue25d",   #
    "text/html":                    "\uf033d",  # 
    "text/css":                     "\uf033c",  # 
    "application/json":             "\uf0226",  # 
    "text/x-c":                     "\ue247",   #
    "text/x-go":                    "\ue724",   #
    "text/x-rust":                  "\ue7a8",   #
    "application/x-sh":             "\ue795",   #
    "text/x-yaml":                  "\uf06fe",  # 
    "application/xml":              "\uf01c0",  # 
    "application/pdf":              "\uf0226",  # 
    "application/zip":              "\uf059b",  # 
    "application/x-tar":            "\uf059b",  # 
    "application/gzip":             "\uf059b",  # 
    "application/x-7z-compressed":  "\uf059b",  # 
    "application/octet-stream":     "\uf0214",  # 
    "unknown":                      "\uf0214",  # 
}

QUICK_LINKS = [
    {"name": "Home",       "path": HOME,                                 "icon": "\uf0035"},  # 
    {"name": "Desktop",    "path": os.path.join(HOME, "Desktop"),        "icon": "\uf03e8"},  # 
    {"name": "Downloads",  "path": os.path.join(HOME, "Downloads"),      "icon": "\uf01da"},  # 
    {"name": "Documents",  "path": os.path.join(HOME, "Documents"),      "icon": "\uf0219"},  # 
    {"name": "Pictures",   "path": os.path.join(HOME, "Pictures"),       "icon": "\uf02e9"},  # 
    {"name": "Videos",     "path": os.path.join(HOME, "Videos"),         "icon": "\uf0177"},  # 
    {"name": "Music",      "path": os.path.join(HOME, "Music"),          "icon": "\uf04d3"},  # 
    {"name": "Projects",   "path": os.path.join(HOME, "Projects"),       "icon": "\ue5fe"},   #
    {"name": "Dotfiles",   "path": os.path.join(HOME, ".dotfiles"),      "icon": "\ue795"},   #
]

def detect_mime(path):
    """Best-effort MIME detection."""
    if os.path.isdir(path):
        return "inode/directory"
    mime, _ = mimetypes.guess_type(path)
    if mime:
        return mime
    try:
        r = subprocess.run(["file", "--mime-type", "-b", path],
                           capture_output=True, text=True, timeout=2)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return "application/octet-stream"

def mime_icon(mime, is_dir=False):
    if is_dir:
        return MIME_ICONS["inode/directory"]
    icon = MIME_ICONS.get(mime)
    if icon:
        return icon
    top = mime.split("/")[0]
    return MIME_ICONS.get(top, MIME_ICONS["unknown"])

def mime_category(mime, is_dir=False):
    if is_dir:
        return "directory"
    if not mime:
        return "other"
    top = mime.split("/")[0]
    if top == "image":  return "image"
    if top == "video":  return "video"
    if top == "audio":  return "audio"
    CODE_MIMES = {
        "text/x-python", "application/javascript", "text/html", "text/css",
        "application/json", "text/x-c", "text/x-c++src", "text/x-java",
        "text/x-go", "text/x-rust", "application/x-sh", "text/x-shellscript",
        "application/x-lua", "text/x-yaml", "application/xml",
    }
    if mime in CODE_MIMES: return "code"
    DOC_MIMES = {
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if mime in DOC_MIMES: return "document"
    if top == "text":   return "text"
    ARCHIVE_MIMES = {
        "application/zip", "application/x-tar", "application/gzip",
        "application/x-bzip2", "application/x-7z-compressed",
    }
    if mime in ARCHIVE_MIMES: return "archive"
    return "other"

def human_size(size):
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def thumbnail_path(path, mime):
    if mime.startswith("image/"):
        try:
            if os.path.getsize(path) < 60 * 1024 * 1024:
                return path
        except OSError:
            pass
        return ""
    if mime.startswith("video/"):
        import hashlib
        h = hashlib.md5(path.encode()).hexdigest()
        thumb = os.path.join(THUMB_DIR, f"{h}.jpg")
        if not os.path.exists(thumb):
            try:
                subprocess.run(
                    ["ffmpegthumbnailer", "-i", path, "-o", thumb, "-s", "128", "-t", "20%"],
                    capture_output=True, timeout=5
                )
            except Exception:
                return ""
        return thumb if os.path.exists(thumb) else ""
    return ""

def cmd_list(args):
    path        = args[0] if args else HOME
    show_hidden = "--hidden" in args
    mime_filter = None
    sort_by     = "name"
    sort_asc    = "--desc" not in args

    for i, a in enumerate(args):
        if a == "--mime" and i + 1 < len(args):
            mime_filter = args[i + 1]
        if a == "--sort" and i + 1 < len(args):
            sort_by = args[i + 1]

    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        print(json.dumps({"error": f"Not a directory: {path}"}))
        return

    entries = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    name = entry.name
                    if not show_hidden and name.startswith("."):
                        continue
                    is_dir  = entry.is_dir(follow_symlinks=True)
                    is_link = entry.is_symlink()
                    st      = entry.stat(follow_symlinks=True)
                    size    = st.st_size if not is_dir else 0
                    mtime   = st.st_mtime
                    mime    = detect_mime(entry.path)
                    cat     = mime_category(mime, is_dir)
                    if mime_filter and mime_filter not in ("all", "") and not is_dir:
                        if cat != mime_filter and not mime.startswith(mime_filter + "/"):
                            continue
                    thumb = thumbnail_path(entry.path, mime) if not is_dir else ""
                    entries.append({
                        "name":        name,
                        "path":        entry.path,
                        "isDir":       is_dir,
                        "isSymlink":   is_link,
                        "size":        size,
                        "sizeStr":     human_size(size) if not is_dir else "",
                        "modified":    mtime,
                        "modifiedStr": datetime.fromtimestamp(mtime).strftime("%b %d %Y  %H:%M"),
                        "mime":        mime,
                        "category":    cat,
                        "icon":        mime_icon(mime, is_dir),
                        "thumbnail":   thumb,
                    })
                except (PermissionError, OSError):
                    continue
    except PermissionError:
        print(json.dumps({"error": "Permission denied"}))
        return

    def file_key(e):
        if sort_by == "size":  return e["size"]
        if sort_by == "date":  return e["modified"]
        return e["name"].lower()

    dirs  = sorted([e for e in entries if e["isDir"]],  key=lambda e: e["name"].lower(), reverse=not sort_asc)
    files = sorted([e for e in entries if not e["isDir"]], key=file_key, reverse=not sort_asc)
    print(json.dumps(dirs + files))

def _load_bookmarks():
    try:
        if os.path.exists(BOOKMARKS_F):
            with open(BOOKMARKS_F) as f:
                return json.load(f)
    except Exception:
        pass
    return []

def _save_bookmarks(bm):
    with open(BOOKMARKS_F, "w") as f:
        json.dump(bm, f, indent=2)

def cmd_bookmarks():
    quick  = [q for q in QUICK_LINKS if os.path.isdir(q["path"])]
    custom = _load_bookmarks()
    print(json.dumps({"quick": quick, "custom": custom}))

def cmd_add_bookmark(path):
    path = os.path.abspath(os.path.expanduser(path))
    bm   = _load_bookmarks()
    if not any(b["path"] == path for b in bm):
        bm.append({"name": os.path.basename(path) or path, "path": path, "icon": "\uf013b"})
        _save_bookmarks(bm)
    print(json.dumps({"ok": True}))

def cmd_remove_bookmark(path):
    path = os.path.abspath(os.path.expanduser(path))
    bm   = [b for b in _load_bookmarks() if b["path"] != path]
    _save_bookmarks(bm)
    print(json.dumps({"ok": True}))

def _load_recents():
    try:
        if os.path.exists(RECENTS_F):
            with open(RECENTS_F) as f:
                return json.load(f)
    except Exception:
        pass
    return []

def _save_recents(r):
    with open(RECENTS_F, "w") as f:
        json.dump(r[:20], f, indent=2)

def cmd_recents():
    print(json.dumps(_load_recents()))

def cmd_add_recent(path):
    path = os.path.abspath(os.path.expanduser(path))
    r    = [x for x in _load_recents() if x["path"] != path]
    r.insert(0, {"name": os.path.basename(path) or path, "path": path, "icon": "\uf013b", "time": time.time()})
    _save_recents(r)
    print(json.dumps({"ok": True}))

def cmd_confirm(paths):
    abs_paths = [os.path.abspath(os.path.expanduser(p)) for p in paths]
    result = {
        "cancelled": False,
        "paths":     abs_paths,
        "uris":      ["file://" + p for p in abs_paths],
        "timestamp": time.time(),
    }
    with open(RESPONSE_F, "w") as f:
        json.dump(result, f)
    if abs_paths:
        try:
            subprocess.run(["wl-copy", "\n".join(abs_paths)], timeout=3)
        except Exception:
            pass
    seen = set()
    for p in abs_paths:
        d = os.path.dirname(p)
        if d and d not in seen and os.path.isdir(d):
            seen.add(d)
            r = [x for x in _load_recents() if x["path"] != d]
            r.insert(0, {"name": os.path.basename(d) or d, "path": d, "icon": "\uf013b", "time": time.time()})
            _save_recents(r)
    print(json.dumps({"ok": True, "count": len(abs_paths)}))

def cmd_cancel():
    result = {"cancelled": True, "timestamp": time.time()}
    with open(RESPONSE_F, "w") as f:
        json.dump(result, f)
    print(json.dumps({"ok": True}))

def cmd_request():
    try:
        if os.path.exists(REQUEST_F):
            with open(REQUEST_F) as f:
                print(f.read())
            return
    except Exception:
        pass
    print(json.dumps({}))

def main():
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "No command given"}))
        return
    cmd  = args[0]
    rest = args[1:]
    if   cmd == "list":            cmd_list(rest)
    elif cmd == "bookmarks":       cmd_bookmarks()
    elif cmd == "add-bookmark":    cmd_add_bookmark(rest[0]) if rest else None
    elif cmd == "remove-bookmark": cmd_remove_bookmark(rest[0]) if rest else None
    elif cmd == "recents":         cmd_recents()
    elif cmd == "add-recent":      cmd_add_recent(rest[0]) if rest else None
    elif cmd == "confirm":         cmd_confirm(rest)
    elif cmd == "cancel":          cmd_cancel()
    elif cmd == "request":         cmd_request()
    elif cmd == "mime":
        if rest: print(detect_mime(rest[0]))
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))

if __name__ == "__main__":
    main()
