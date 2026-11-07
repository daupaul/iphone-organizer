# iphone-organizer

Reorganize a **personal (non‑supervised) iPhone** home screen from your Mac,
driving Apple's built‑in **iPhone Mirroring** (macOS Sequoia+ / iOS 18+) with
synthetic mouse + keyboard events. No USB cable, no supervision, no jailbreak,
no MDM. The phone is never wiped.

> Why this exists: Apple Configurator can batch‑arrange a home screen but only on
> a **supervised** device (which erases it). The only no‑USB path is iPhone
> Mirroring, and existing OSS only offers generic tap/swipe. This adds the parts
> that were missing: **grid calibration, Screen‑Time‑aware planning, and reliable
> folder/drag/rename/remove verbs with a defined workflow.**

## Requirements
- macOS with **iPhone Mirroring** open and connected; iPhone unlocked once, then
  left locked and untouched (using the phone drops the mirror).
- Terminal granted **Accessibility** + **Screen Recording** permissions.
- `swiftc` (Xcode CLT). Build once: `swiftc -O hsctl.swift -o hsctl`.

## Pieces
- `hsctl` — compiled Swift binary. Low‑level CGEvent primitives (tap, press,
  drag, dragout, scroll, key, paste, selall). Coordinates are **screen points**.
- `hs.py` — calibration + grid model + high‑level verbs; auto‑detects the mirror
  window every call so it survives the window moving.

## Calibration (confirm the mirror coordinates)
`hs.py` detects the window with AppleScript and maps a **4‑column grid** using
fractions in `CAL` (calibrated for an iPhone 15/16‑class portrait mirror).
Check it: `python3 hs.py geom` then `python3 hs.py slotpt 0 0`. If slots miss the
icons on your device, tweak `CAL` (`cols_xf`, `row0_yf`, `row_dyf`, `dock_yf`).

## Workflow
1. **Calibrate** — verify `slot(r,c)` lands on icons.
2. **Inventory** — `hs.py shot p1.png`, `swipe left`, repeat across pages + App
   Library. Understand everything installed.
3. **Usage** — open Settings → Screen Time → *See All App & Website Activity* →
   *Week*; screenshot the Most‑Used + Pickups lists. Let real usage pick page 1.
4. **Plan** — page 1 = a **full page of the most‑used apps, no folders**; page 2 =
   function folders (Comms / Finance / Work / Media / Sports / Travel / Tools /
   Games); page 3 = country folders. One rule removes ambiguity: *an app that is
   only useful in one country goes in that country's folder; everything global
   goes in its function folder.*
5. **Execute** — verbs below. Work a page at a time; same‑page drags are the most
   reliable, cross‑page the least.
6. **Verify** — screenshot each page; fix misplacements.

## Verbs (`python3 hs.py <verb> ...`)
| verb | meaning |
|---|---|
| `geom` | print window origin+size |
| `shot FILE` | screenshot the mirror window |
| `slot R C` / `tap X Y` | tap a grid slot / a raw point |
| `press X Y [SEC]` | long‑press → context menu (≈1.4s) |
| `home` / `swipe left\|right` / `scroll down\|up` | navigation |
| `folder R1 C1 R2 C2` | drag app onto app/folder → **create/add to folder** |
| `move R1 C1 R2 C2` | reposition an icon to an empty slot |
| `dragout X Y R C` | pull an app **out of an open folder** to a page slot |
| `rename TEXT` | in an open folder (jiggle, name focused) → replace the name |
| `confirm` | tap "Remove from Home Screen" in the removal dialog |
| `done` | exit jiggle mode |

## Reliability notes (learned on real hardware)
- **Drag‑to‑folder works great**; the tiny jiggle "−" badge is too small to hit —
  remove via long‑press → *Remove App* → `confirm` instead.
- Keep context‑menu taps **in one shell call**; menus auto‑dismiss between calls.
- `dragout` drags down past the folder boundary (`exit_yf`) first, then places —
  dragging below the window fails, so stay within window bounds.
- Removing from Home keeps the app in the App Library (searchable); it is never
  deleted. Deleting apps is intentionally not automated.

## Status / license
Prototype, MIT. CGEvent injection works on this setup; some reports say iPhone
Mirroring can block it (then a Karabiner virtual‑HID backend is needed).
