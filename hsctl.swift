// hsctl — low-level input/output primitives for driving macOS "iPhone Mirroring"
// via synthetic mouse/keyboard events. Coordinates are SCREEN POINTS.
// Subcommands:
//   tap X Y
//   press X Y SECONDS                       (long-press -> context menu / jiggle)
//   drag X1 Y1 X2 Y2 PICKUP HOVER           (pick up, move, hover, drop; folder/add)
//   dragout X1 Y1 X2 Y2 EXITY               (pull app out of open folder onto page)
//   scroll X Y DX DY COUNT                  (DX/DY per step, pixel units)
//   key NAME                                (home|appswitch|spotlight)
//   paste TEXT...                           (set clipboard, send Cmd+V)
//   selall                                  (Cmd+A)
import CoreGraphics
import AppKit
import Foundation

func post(_ t: CGEventType, _ p: CGPoint) {
  CGEvent(mouseEventSource: nil, mouseType: t, mouseCursorPosition: p, mouseButton: .left)?.post(tap: .cghidEventTap)
}
func moveTo(_ p: CGPoint) { post(.mouseMoved, p) }
func sleepMs(_ ms: UInt32) { usleep(ms * 1000) }

func tap(_ x: Double, _ y: Double) {
  let p = CGPoint(x: x, y: y)
  moveTo(p); sleepMs(120)
  post(.leftMouseDown, p); sleepMs(70)
  post(.leftMouseUp, p); sleepMs(120)
}
func press(_ x: Double, _ y: Double, _ sec: Double) {
  let p = CGPoint(x: x, y: y)
  moveTo(p); sleepMs(150)
  post(.leftMouseDown, p)
  sleepMs(UInt32(sec * 1000))
  post(.leftMouseUp, p); sleepMs(200)
}
func lineDrag(_ a: CGPoint, _ b: CGPoint, _ steps: Int, _ stepMs: UInt32) {
  for i in 1...steps {
    let t = Double(i) / Double(steps)
    post(.leftMouseDragged, CGPoint(x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t))
    sleepMs(stepMs)
  }
}
func drag(_ x1: Double,_ y1: Double,_ x2: Double,_ y2: Double,_ pickup: Double,_ hover: Double) {
  let s = CGPoint(x: x1, y: y1), e = CGPoint(x: x2, y: y2)
  moveTo(s); sleepMs(200)
  post(.leftMouseDown, s); sleepMs(UInt32(pickup * 1000))
  post(.leftMouseDragged, CGPoint(x: x1 + 3, y: y1 + 3)); sleepMs(150)
  lineDrag(s, e, 18, 32)
  sleepMs(UInt32(hover * 1000))
  post(.leftMouseUp, e); sleepMs(400)
}
func dragout(_ x1: Double,_ y1: Double,_ x2: Double,_ y2: Double,_ exitY: Double) {
  let s = CGPoint(x: x1, y: y1)
  moveTo(s); sleepMs(200)
  post(.leftMouseDown, s); sleepMs(800)
  post(.leftMouseDragged, CGPoint(x: x1 + 3, y: y1 + 3)); sleepMs(150)
  let mid = CGPoint(x: x1, y: exitY)       // cross folder boundary -> exits folder
  lineDrag(s, mid, 14, 35); sleepMs(1000)  // let folder close
  lineDrag(mid, CGPoint(x: x2, y: y2), 12, 35); sleepMs(800)
  post(.leftMouseUp, CGPoint(x: x2, y: y2)); sleepMs(400)
}
func scroll(_ x: Double,_ y: Double,_ dx: Int32,_ dy: Int32,_ count: Int) {
  let p = CGPoint(x: x, y: y); moveTo(p); sleepMs(150)
  for _ in 0..<count {
    if let e = CGEvent(scrollWheelEvent2Source: nil, units: .pixel, wheelCount: 2, wheel1: dy, wheel2: dx, wheel3: 0) {
      e.location = p; e.post(tap: .cghidEventTap)
    }
    sleepMs(9)
  }
  sleepMs(400)
}
func keyStroke(_ vk: CGKeyCode, _ flags: CGEventFlags) {
  let d = CGEvent(keyboardEventSource: nil, virtualKey: vk, keyDown: true)!
  d.flags = flags; d.post(tap: .cghidEventTap); sleepMs(40)
  let u = CGEvent(keyboardEventSource: nil, virtualKey: vk, keyDown: false)!
  u.flags = flags; u.post(tap: .cghidEventTap); sleepMs(120)
}

let a = CommandLine.arguments
func d(_ i: Int) -> Double { return Double(a[i])! }
guard a.count > 1 else { print("usage: hsctl <cmd> ..."); exit(1) }
switch a[1] {
case "tap":     tap(d(2), d(3))
case "press":   press(d(2), d(3), d(4))
case "drag":    drag(d(2), d(3), d(4), d(5), d(6), d(7))
case "dragout": dragout(d(2), d(3), d(4), d(5), d(6))
case "scroll":  scroll(d(2), d(3), Int32(a[4])!, Int32(a[5])!, Int(a[6])!)
case "key":
  switch a[2] {
    case "home":     keyStroke(18, .maskCommand)      // Cmd+1
    case "appswitch":keyStroke(19, .maskCommand)      // Cmd+2
    case "spotlight":keyStroke(20, .maskCommand)      // Cmd+3
    default: break
  }
case "selall":  keyStroke(0, .maskCommand)            // Cmd+A
case "paste":
  let text = a[2...].joined(separator: " ")
  let pb = NSPasteboard.general; pb.clearContents(); pb.setString(text, forType: .string)
  sleepMs(120); keyStroke(9, .maskCommand)            // Cmd+V
default: print("unknown cmd \(a[1])"); exit(1)
}
