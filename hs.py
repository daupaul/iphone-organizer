#!/usr/bin/env python3
"""
hs.py — iPhone Mirroring home-screen control (calibration + grid model + verbs).

Pairs with the compiled ./hsctl binary (low-level CGEvent input + clipboard).
All coordinates are macOS SCREEN POINTS. The iPhone-Mirroring window geometry is
auto-detected every call (via AppleScript), so the tool survives the window being
moved. Grid slot positions are expressed as fractions of the window and were
calibrated on an iPhone 15/16-class portrait mirror; recalibrate CAL for other
devices with `hs.py calibrate`.

Workflow (see README):
  1. calibrate  — verify the grid lands on icons
  2. inventory  — screenshot every page + App Library (understand what's installed)
  3. usage      — open Screen Time, read weekly most-used (understand app usage)
  4. plan       — decide page1 (full, no folders) / page2 function folders / page3 country
  5. execute    — folder/drag/dragout/rename/remove verbs
  6. verify     — screenshot each page after
"""
import subprocess, sys, os, time, json

HERE = os.path.dirname(os.path.abspath(__file__))
HSCTL = os.path.join(HERE, "hsctl")
PROC = "iPhone Mirroring"

# --- calibration: fractions of the mirror window (origin+size in points) -------
CAL = {
    "cols_xf": [0.177, 0.389, 0.608, 0.821],   # 4 column centers
    "row0_yf": 0.412,                           # first app row center
    "row_dyf": 0.104,                           # vertical spacing between rows
    "nrows": 5,                                 # app rows above the dock
    "dock_yf": 0.910,                           # dock row center
    "exit_yf": 0.86,                            # y to drag to when pulling out of a folder
    "confirm_yf": 0.274,                        # "Remove from Home Screen" button (both dialog types)
    "done_xf": 0.815, "done_yf": 0.078,         # jiggle-mode Done (checkmark)
}

def geom():
    """Return (ox, oy, w, h) of the iPhone Mirroring window in points."""
    scr = (f'tell application "System Events" to tell process "{PROC}" to '
           f'get {{position, size}} of window 1')
    out = subprocess.run(["osascript", "-e", scr], capture_output=True, text=True)
    if out.returncode != 0 or not out.stdout.strip():
        raise RuntimeError("iPhone Mirroring window not found. Is it open & connected?")
    nums = [int(x) for x in out.stdout.replace(",", " ").split()]
    return nums[0], nums[1], nums[2], nums[3]

def focus():
    subprocess.run(["osascript", "-e",
        f'tell application "System Events" to set frontmost of process "{PROC}" to true'],
        capture_output=True)
    time.sleep(0.25)

def _pt_from_frac(xf, yf):
    ox, oy, w, h = geom()
    return ox + xf * w, oy + yf * h

def slot(r, c):
    """Screen point of app-grid slot row r (0..nrows-1), col c (0..3)."""
    return _pt_from_frac(CAL["cols_xf"][c], CAL["row0_yf"] + CAL["row_dyf"] * r)

def dock(c):
    return _pt_from_frac(CAL["cols_xf"][c], CAL["dock_yf"])

def hsctl(*args):
    subprocess.run([HSCTL, *[str(a) for a in args]], check=False)

# --- primitives ----------------------------------------------------------------
def shot(path):
    ox, oy, w, h = geom()
    subprocess.run(["screencapture", "-x", f"-R{ox},{oy},{w},{h}", path], check=False)
    return path

def tap(x, y):            focus(); hsctl("tap", x, y)
def tap_slot(r, c):       x, y = slot(r, c); tap(x, y)
def press(x, y, sec=1.4): focus(); hsctl("press", x, y, sec)
def home():               focus(); hsctl("key", "home")
def swipe(direction):
    focus(); ox, oy, w, h = geom()
    cx, cy = ox + 0.5 * w, oy + 0.42 * h
    dx = -26 if direction == "left" else 26
    hsctl("scroll", cx, cy, dx, 0, 12)
def scroll_v(direction, count=12):
    focus(); ox, oy, w, h = geom()
    cx, cy = ox + 0.5 * w, oy + 0.42 * h
    dy = -22 if direction == "down" else 22
    hsctl("scroll", cx, cy, 0, dy, count)

def folder(r1, c1, r2, c2):
    """Drag app at (r1,c1) ONTO app/folder at (r2,c2): create folder or add to it."""
    focus(); x1, y1 = slot(r1, c1); x2, y2 = slot(r2, c2)
    hsctl("drag", x1, y1, x2, y2, 0.8, 1.3)
def move(r1, c1, r2, c2):
    """Reposition an icon to an empty slot (short hover = no folder)."""
    focus(); x1, y1 = slot(r1, c1); x2, y2 = slot(r2, c2)
    hsctl("drag", x1, y1, x2, y2, 0.8, 0.3)
def dragout(x1, y1, r2, c2):
    """Pull an app OUT of an OPEN folder (pixel src) to page slot (r2,c2)."""
    focus(); x2, y2 = slot(r2, c2)
    ox, oy, w, h = geom(); exitY = oy + CAL["exit_yf"] * h
    hsctl("dragout", x1, y1, x2, y2, exitY)

def confirm_remove():
    """Tap the 'Remove from Home Screen' button in the removal dialog."""
    x, y = _pt_from_frac(0.5, CAL["confirm_yf"]); tap(x, y)
def done():
    """Exit jiggle mode (tap the checkmark)."""
    x, y = _pt_from_frac(CAL["done_xf"], CAL["done_yf"]); tap(x, y)

def rename(text):
    """In an OPEN folder in jiggle mode with the name field focused: replace name."""
    focus(); hsctl("selall"); time.sleep(0.2); hsctl("paste", text)

# --- CLI -----------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd, a = sys.argv[1], sys.argv[2:]
    if   cmd == "geom":    print(geom())
    elif cmd == "shot":    print(shot(a[0]))
    elif cmd == "tap":     tap(float(a[0]), float(a[1]))
    elif cmd == "slot":    tap_slot(int(a[0]), int(a[1]))
    elif cmd == "press":   press(float(a[0]), float(a[1]), float(a[2]) if len(a)>2 else 1.4)
    elif cmd == "home":    home()
    elif cmd == "swipe":   swipe(a[0])
    elif cmd == "scroll":  scroll_v(a[0], int(a[1]) if len(a)>1 else 12)
    elif cmd == "folder":  folder(int(a[0]),int(a[1]),int(a[2]),int(a[3]))
    elif cmd == "move":    move(int(a[0]),int(a[1]),int(a[2]),int(a[3]))
    elif cmd == "dragout": dragout(float(a[0]),float(a[1]),int(a[2]),int(a[3]))
    elif cmd == "confirm": confirm_remove()
    elif cmd == "done":    done()
    elif cmd == "rename":  rename(" ".join(a))
    elif cmd == "slotpt":  print(slot(int(a[0]),int(a[1])))
    else: print("unknown:", cmd)

if __name__ == "__main__":
    main()
