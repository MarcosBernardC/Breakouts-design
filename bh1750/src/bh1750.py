import FreeCAD as App
import Part
import Import
import os

import Draft

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
    # Asegurar color simple
    if "Color" not in obj.PropertiesList:
        obj.addProperty("App::PropertyColor", "Color", "Base", "Object color")
    obj.Color = tuple(rgb)

    # Asegurar DiffuseColor persistente (VRML la usa)
    if "DiffuseColor" not in obj.PropertiesList:
        obj.addProperty("App::PropertyColorList", "DiffuseColor", "Base", "Face colors")

    obj.DiffuseColor = [tuple(rgb)]  # 1 solo color para todo el sólido

    # Pintar GUI si existe
    if GUI and hasattr(obj, "ViewObject"):
        obj.ViewObject.ShapeColor = tuple(rgb)
        obj.ViewObject.DiffuseColor = [tuple(rgb)]




# ============================
#   CONFIGURACIÓN GENERAL
# ============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "build"))
os.makedirs(BUILD_DIR, exist_ok=True)

# ============================
#   PARÁMETROS PCB (BH1750)
# ============================
L = 18.0
A = 13.0
E = 1.2

pcb_color = (0.082, 0.353, 0.384)

# ============================
#   DOCUMENTO
# ============================
DOC = App.newDocument("BH1750_PCB")

# ============================
#   PCB BASE
# ============================
pcb = Part.makeBox(L, A, E)

pcb_obj = DOC.addObject("Part::Feature", "PCB")
pcb_obj.Shape = pcb
pcb_obj.addProperty("App::PropertyColor", "Color", "Base", "Object color")
pcb_obj.Color = pcb_color
safe_color(pcb_obj, pcb_color)

# ============================
#   PARÁMETROS PINES
# ============================
N_PINS = 5
PIN_SIZE = 0.64
PIN_LEN  = 11.0
PIN_PITCH = 2.54
PIN_NAMES = ["ADDR", "SDA", "SCL", "GND", "VCC"]

EDGE_X = 1.5
GROUP_LEN = (N_PINS - 1) * PIN_PITCH
py0 = (A - GROUP_LEN) / 2

# ============================
#   METADATOS (PINMETA)
# ============================
pinmeta = DOC.addObject("App::FeaturePython", "PinMeta")
pinmeta.addProperty("App::PropertyStringList", "Names", "Pinout", "Pin names")
pinmeta.Names = PIN_NAMES

# ============================
#   HOLES (PRIMERO)
# ============================
HOLE_DIAM = 0.9
HOLE_R = HOLE_DIAM / 2

hole_shapes = []
for i in range(N_PINS):
    cx = EDGE_X
    cy = py0 + i * PIN_PITCH
    hole = Part.makeCylinder(HOLE_R, E)
    hole.translate(App.Vector(cx, cy, 0))
    hole_shapes.append(hole)

pcb_cut = pcb_obj.Shape
for h in hole_shapes:
    pcb_cut = pcb_cut.cut(h)

pcb_obj.Shape = pcb_cut

# ============================
#   ANILLOS DE SOLDADURA (PADS)
# ============================

PAD_OD = 1.6          # diámetro exterior del pad (BH1750 breakout típico)
PAD_R  = PAD_OD / 2
PAD_H  = 0.05         # espesor visual del anillo

INNER_D = HOLE_DIAM   # mismo diámetro que el hole
INNER_R = INNER_D / 2

pad_objs = []

for i in range(N_PINS):
    cx = EDGE_X
    cy = py0 + i * PIN_PITCH

    # cilindros concéntricos
    outer = Part.makeCylinder(PAD_R, PAD_H)
    inner = Part.makeCylinder(INNER_R, PAD_H)

    # anillo final
    ring = outer.cut(inner)

    # colocar justo arriba de la PCB
    ring.translate(App.Vector(cx, cy, E))

    pad = DOC.addObject("Part::Feature", f"Pad_{PIN_NAMES[i]}")
    pad.Shape = ring

    # color cobre/dorado
    safe_color(pad, (0.80, 0.75, 0.65))

    pad_objs.append(pad)

# ============================
#   PINES (DESPUÉS DE HOLES)
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

    p_obj = DOC.addObject("Part::Feature", f"Pin_{PIN_NAMES[i]}")
    p_obj.Shape = pin

    # Color
    p_obj.addProperty("App::PropertyColor", "Color", "Base", "Object color")
    p_obj.Color = (0.9, 0.85, 0.3)
    safe_color(p_obj, (0.9, 0.85, 0.3))

    # ============================
    #   METADATO INDIVIDUAL DEL PIN
    # ============================
    p_obj.addProperty("App::PropertyString", "PinName", "PinData", "Pin name")
    p_obj.PinName = PIN_NAMES[i]

    pin_objs.append(p_obj)

# ============================
#   HOUSING DEL HEADER (3D)
# ============================
HOUSING_W = 2
HOUSING_H = 2
HOUSING_MARGIN = 0.6

WING_EXTRA = 0.4
WING_THICK = HOUSING_W
WING_HEIGHT = HOUSING_H

housing_len = GROUP_LEN + HOUSING_MARGIN

housing_y = py0 + GROUP_LEN / 2 - housing_len / 2
housing_x = EDGE_X - HOUSING_W / 2
housing_z = -HOUSING_H

housing_main = Part.makeBox(HOUSING_W, housing_len, HOUSING_H)
housing_main.translate(App.Vector(housing_x, housing_y, housing_z))

wing1 = Part.makeBox(WING_THICK, WING_EXTRA, WING_HEIGHT)
wing1.translate(App.Vector(housing_x, housing_y - WING_EXTRA, housing_z))

wing2 = Part.makeBox(WING_THICK, WING_EXTRA, WING_HEIGHT)
wing2.translate(App.Vector(housing_x, housing_y + housing_len, housing_z))

housing_shape = housing_main.fuse(wing1).fuse(wing2)

housing_obj = DOC.addObject("Part::Feature", "HeaderHousing")
housing_obj.Shape = housing_shape
safe_color(housing_obj, (0.05, 0.05, 0.05))

# ============================
#   HOLES PARA PERNOS
# ============================
MOUNT_DIAM = 3
MOUNT_R = MOUNT_DIAM / 2

mx1, my1 = 15.5, 2.5
mx2, my2 = 15.5, 10.50

mount1 = Part.makeCylinder(MOUNT_R, E)
mount1.translate(App.Vector(mx1, my1, 0))

mount2 = Part.makeCylinder(MOUNT_R, E)
mount2.translate(App.Vector(mx2, my2, 0))

pcb_cut2 = pcb_obj.Shape
pcb_cut2 = pcb_cut2.cut(mount1)
pcb_cut2 = pcb_cut2.cut(mount2)

pcb_obj.Shape = pcb_cut2

# ============================
#   SENSOR BH1750 (TRANSDUCTOR ÓPTICO)
# ============================
S_W = 3.8
S_L = 3.8
S_H = 1.1

WIN_W = 2.2
WIN_L = 1.4
WIN_H = 0.25
WIN_INSET = 0.05

scx = L/2 - S_W/2 + 1.5
scy = A/2 - S_L/2
scz = E

chip = Part.makeBox(S_W, S_L, S_H)
chip.translate(App.Vector(scx, scy, scz))

chip_obj = DOC.addObject("Part::Feature", "BH1750_Chip")
chip_obj.Shape = chip
safe_color(chip_obj, (0.05, 0.05, 0.07))

win_x = L/2 - WIN_W/2 + 1.5
win_y = A/2 - WIN_L/2
win_z = scz + S_H - WIN_H + WIN_INSET

window = Part.makeBox(WIN_W, WIN_L, WIN_H)
window.translate(App.Vector(win_x, win_y, win_z))

try:
    window = window.makeFillet(0.12, window.Edges)
except:
    pass

window_obj = DOC.addObject("Part::Feature", "BH1750_Window")
window_obj.Shape = window
safe_color(window_obj, (0.3, 0.7, 0.95))

# --------------------------------------
# LABELS sobre la PCB (BH1750) — MISMA LÓGICA x0/dx/y0/dy — SIN rotación
# --------------------------------------

FONT = "/usr/share/fonts/TTF/DejaVuSans.ttf"

# lógica estilo BME280: array horizontal desplazado
x0 = EDGE_X + 1.5     # ajustable
dx = 0              # separación horizontal entre labels
y0 = 11.0              # altura base del texto
dy = -2.5               # no variamos Y en este caso (fila horizontal)

LABEL_SIZE = 1.0
LABEL_Z = E

# Usamos tu orden de pines BH1750
labels = [
    ("ADDR", "LBL_ADDR"),
    ("SDA",  "LBL_SDA"),
    ("SCL",  "LBL_SCL"),
    ("GND",  "LBL_GND"),
    ("VCC",  "LBL_VCC")
]

for i, (text, name) in enumerate(labels):

    pos = App.Vector(
        x0 + i*dx,
        y0 + i*dy,
        LABEL_Z
    )

    txt = Draft.makeShapeString(
        String=text,
        FontFile=FONT,
        Size=LABEL_SIZE,
        Tracking=0
    )

    # posición SIN rotación — coherente con tu petición
    txt.Placement = App.Placement(
        pos,
        App.Rotation()
    )

    DOC.recompute()

    solid = txt.Shape.extrude(App.Vector(0, 0, 0.03))

    obj = DOC.addObject("Part::Feature", name)
    obj.Shape = solid
    safe_color(obj, (0.99, 0.99, 0.99))

# ============================
#   RECOMPUTE
# ============================
DOC.recompute()

# ============================
#   EXPORT
# ============================
fcstd_path = os.path.join(BUILD_DIR, "bh1750.FCStd")
stl_path  = os.path.join(BUILD_DIR, "bh1750.stl")

DOC.saveAs(fcstd_path)
Import.export([pcb_obj], stl_path)

print("✔ BH1750 PCB generado:")
print("   FCStd:", fcstd_path)
print("   STL :", stl_path)

if GUI:
    try:
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    except:
        pass
