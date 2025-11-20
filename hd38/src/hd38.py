import FreeCAD as App
import Part
import Import
import os

# ============================
#   DETECTAR GUI
# ============================
GUI = App.GuiUp
if GUI:
    import FreeCADGui as Gui

# ============================
#   UTILIDAD: COLOR SEGURO
# ============================
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

# ============================
#   CONFIG GENERAL
# ============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "build"))
os.makedirs(BUILD_DIR, exist_ok=True)

# ============================
#   PARÁMETROS PCB HD-38
# ============================
L = 30.0
A = 15.0
E = 1.2

pcb_color = (0.03, 0.03, 0.03)

# ============================
#   DOCUMENTO
# ============================
DOC = App.newDocument("HD38_PCB")

# ============================
#   PCB BASE
# ============================
pcb = Part.makeBox(L, A, E)
pcb_obj = DOC.addObject("Part::Feature", "PCB")
pcb_obj.Shape = pcb
safe_color(pcb_obj, pcb_color)

# ============================
#   PINES
# ============================
PIN_NAMES = ["+", "-", "DO", "AO"]
N_PINS = len(PIN_NAMES)

PIN_SIZE = 0.64
PIN_LEN  = 11.0
PIN_PITCH = 2.54

EDGE_X = 1.5
GROUP_LEN = (N_PINS - 1) * PIN_PITCH
py0 = (A - GROUP_LEN) / 2

# ============================
#   METADATOS PINES
# ============================
pinmeta = DOC.addObject("App::FeaturePython", "PinMeta")
pinmeta.addProperty("App::PropertyStringList", "Names", "Pinout", "Pin names")
pinmeta.Names = PIN_NAMES

# ============================
#   HOLES
# ============================
HOLE_DIAM = 0.9
HOLE_R = HOLE_DIAM / 2

hole_shapes = []
for i in range(N_PINS):
    cx = EDGE_X
    cy = py0 + i * PIN_PITCH
    h = Part.makeCylinder(HOLE_R, E)
    h.translate(App.Vector(cx, cy, 0))
    hole_shapes.append(h)

pcb_cut = pcb_obj.Shape
for h in hole_shapes:
    pcb_cut = pcb_cut.cut(h)
pcb_obj.Shape = pcb_cut

# ============================
#   PADS
# ============================
PAD_OD = 1.6
PAD_R = PAD_OD / 2
PAD_H = 0.05

INNER_R = HOLE_R

pad_objs = []
for i in range(N_PINS):
    cx = EDGE_X
    cy = py0 + i * PIN_PITCH

    outer = Part.makeCylinder(PAD_R, PAD_H)
    inner = Part.makeCylinder(INNER_R, PAD_H)
    ring = outer.cut(inner)

    ring.translate(App.Vector(cx, cy, E))

    pad = DOC.addObject("Part::Feature", f"Pad_{PIN_NAMES[i]}")
    pad.Shape = ring
    safe_color(pad, (0.80, 0.75, 0.65))
    pad_objs.append(pad)

# ============================
#   PINES 3D
# ============================
pin_objs = []
for i in range(N_PINS):
    hx = EDGE_X
    hy = py0 + i * PIN_PITCH

    px = hx - PIN_SIZE / 2
    py = hy - PIN_SIZE / 2
    pz = - (PIN_LEN - E - 1.5)

    pin = Part.makeBox(PIN_SIZE, PIN_SIZE, PIN_LEN)
    pin.translate(App.Vector(px, py, pz))

    po = DOC.addObject("Part::Feature", f"Pin_{PIN_NAMES[i]}")
    po.Shape = pin
    safe_color(po, (0.9, 0.85, 0.3))

    po.addProperty("App::PropertyString", "PinName", "PinData", "Pin name")
    po.PinName = PIN_NAMES[i]

    pin_objs.append(po)

# ============================
#   HOUSING DEL HEADER
# ============================
HOUSING_W = 2
HOUSING_H = 2
HOUSING_MARGIN = 0.6

WING_EXTRA = 0.4
WING_THICK = HOUSING_W
WING_HEIGHT = HOUSING_H

housing_len = GROUP_LEN + HOUSING_MARGIN
housing_y = py0 + GROUP_LEN/2 - housing_len/2
housing_x = EDGE_X - HOUSING_W/2
housing_z = -HOUSING_H

main = Part.makeBox(HOUSING_W, housing_len, HOUSING_H)
main.translate(App.Vector(housing_x, housing_y, housing_z))

w1 = Part.makeBox(WING_THICK, WING_EXTRA, WING_HEIGHT)
w1.translate(App.Vector(housing_x, housing_y - WING_EXTRA, housing_z))

w2 = Part.makeBox(WING_THICK, WING_EXTRA, WING_HEIGHT)
w2.translate(App.Vector(housing_x, housing_y + housing_len, housing_z))

housing_shape = main.fuse(w1).fuse(w2)

hobj = DOC.addObject("Part::Feature", "HeaderHousing")
hobj.Shape = housing_shape
safe_color(hobj, (0.85, 0.91, 0.05))

# ============================
#   RECOMPUTE
# ============================
DOC.recompute()

# ============================
#   EXPORT
# ============================
fcstd_path = os.path.join(BUILD_DIR, "hd38.FCStd")
stl_path  = os.path.join(BUILD_DIR, "hd38.stl")

DOC.saveAs(fcstd_path)
Import.export([pcb_obj], stl_path)

print("✔ HD-38 v1.0 generada:")
print("   FCStd:", fcstd_path)
print("   STL :", stl_path)

if GUI:
    try:
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    except:
        pass
