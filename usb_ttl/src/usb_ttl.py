import FreeCAD as App
import Part
import Import
import os

# ============================
#   TTL-USB BASE: SOLO PCB + PINES + PADS
#   PCB: 15 x 30 mm (negra)
# ============================

GUI = App.GuiUp
if GUI:
    import FreeCADGui as Gui

# --------------------------------------
# COLOR SEGURO
# --------------------------------------
def safe_color(obj, rgb):
    if "Color" not in obj.PropertiesList:
        obj.addProperty("App::PropertyColor", "Color", "Base", "Object color")
    obj.Color = tuple(rgb)

    if "DiffuseColor" not in obj.PropertiesList:
        obj.addProperty("App::PropertyColorList", "DiffuseColor", "Base", "Face colors")
    obj.DiffuseColor = [tuple(rgb)]

    if GUI and hasattr(obj, "ViewObject"):
        obj.ViewObject.ShapeColor = tuple(rgb)
        obj.ViewObject.DiffuseColor = [tuple(rgb)]

# --------------------------------------
# PATHS
# --------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "build"))
os.makedirs(BUILD_DIR, exist_ok=True)

# --------------------------------------
# PCB (15 x 30 mm)
# --------------------------------------
L = 30.0
A = 15.0
E = 1.6
pcb_color = (0.03, 0.03, 0.03)

DOC = App.newDocument("TTL_USB_BASE")

pcb = Part.makeBox(L, A, E)
pcb_obj = DOC.addObject("Part::Feature", "PCB")
pcb_obj.Shape = pcb
safe_color(pcb_obj, pcb_color)

# --------------------------------------
# HEADER DE 6 PINES: VCC, GND, TX, RX, RTS, DTR
# --------------------------------------
PIN_NAMES = ["VCC", "GND", "TX", "RX", "RTS", "DTR"]
N_PINS = len(PIN_NAMES)

PIN_SIZE = 0.64
PIN_LEN  = 11.0
PIN_PITCH = 2.00
EDGE_X = 3.0
GROUP_LEN = (N_PINS - 1) * PIN_PITCH
py0 = (A - GROUP_LEN) / 2

HOLE_DIAM = 0.9
HOLE_R = HOLE_DIAM / 2
PAD_OD = 1.6
PAD_R = PAD_OD / 2
PAD_H = 0.05
INNER_R = HOLE_R

pinmeta = DOC.addObject("App::FeaturePython", "PinMeta")
pinmeta.addProperty("App::PropertyStringList", "Names", "Pinout", "Pin names")
pinmeta.Names = PIN_NAMES

# --- holes + pads + pines ---
for i in range(N_PINS):
    cx = EDGE_X
    cy = py0 + i * PIN_PITCH

    # agujero pasante
    h = Part.makeCylinder(HOLE_R, E)
    h.translate(App.Vector(cx, cy, 0))
    pcb_obj.Shape = pcb_obj.Shape.cut(h)

    # pad superior anular
    outer = Part.makeCylinder(PAD_R, PAD_H)
    inner = Part.makeCylinder(INNER_R, PAD_H)
    ring = outer.cut(inner)
    ring.translate(App.Vector(cx, cy, E))

    pad = DOC.addObject("Part::Feature", f"Pad_{PIN_NAMES[i]}")
    pad.Shape = ring
    safe_color(pad, (0.80, 0.75, 0.65))

    # pin 3D
    px = cx - PIN_SIZE/2
    py = cy - PIN_SIZE/2
    pz = -(PIN_LEN - E - 1.5)

    pin = Part.makeBox(PIN_SIZE, PIN_SIZE, PIN_LEN)
    pin.translate(App.Vector(px, py, pz))

    po = DOC.addObject("Part::Feature", f"Pin_{PIN_NAMES[i]}")
    po.Shape = pin
    safe_color(po, (0.90, 0.85, 0.30))
    po.addProperty("App::PropertyString", "PinName", "PinData", "Pin name")
    po.PinName = PIN_NAMES[i]

# --------------------------------------
# FINAL
# --------------------------------------
DOC.recompute()

fcstd_path = os.path.join(BUILD_DIR, "ttl_usb_base.FCStd")
stl_path  = os.path.join(BUILD_DIR, "ttl_usb_base.stl")

DOC.saveAs(fcstd_path)
Import.export([pcb_obj], stl_path)

print("✔ TTL-USB base generada:")
print("   FCStd:", fcstd_path)
print("   STL :", stl_path)

if GUI:
    try:
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    except:
        pass
# === USB-A Male Placeholder ===
usb = DOC.addObject("Part::Box", "USB_A_Male")
usb.Length = 19
usb.Width = 13
usb.Height = 4.5
usb.Placement.Base = App.Vector(18, 1, 1.6)
safe_color(usb, (0.8,0.8,0.85))



