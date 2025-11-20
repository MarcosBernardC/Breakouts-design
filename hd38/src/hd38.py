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
#   PINES PRINCIPALES
# ============================
PIN_NAMES = ["+", "-", "DO", "AO"]
N_PINS = len(PIN_NAMES)

PIN_SIZE = 0.64
PIN_LEN  = 11.0
PIN_PITCH = 2.54

EDGE_X = 3
GROUP_LEN = (N_PINS - 1) * PIN_PITCH
py0 = (A - GROUP_LEN) / 2

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
    pcb_obj.Shape = pcb_obj.Shape.cut(h)

# ============================
#   PADS
# ============================
PAD_OD = 1.6
PAD_R = PAD_OD / 2
PAD_H = 0.05
INNER_R = HOLE_R

for i in range(N_PINS):
    cx = EDGE_X
    cy = py0 + i * PIN_PITCH

    o = Part.makeCylinder(PAD_R, PAD_H)
    ii = Part.makeCylinder(INNER_R, PAD_H)
    ring = o.cut(ii)
    ring.translate(App.Vector(cx, cy, E))

    pad = DOC.addObject("Part::Feature", f"Pad_{PIN_NAMES[i]}")
    pad.Shape = ring
    safe_color(pad, (0.80, 0.75, 0.65))

# ============================
#   PINES 3D (rectos)
# ============================
for i in range(N_PINS):
    hx = EDGE_X
    hy = py0 + i * PIN_PITCH

    px = hx - PIN_SIZE / 2
    py = hy - PIN_SIZE / 2
    pz = -(PIN_LEN - E - 1.5)

    # sin dimensiones negativas
    pin = Part.makeBox(PIN_SIZE, PIN_SIZE, PIN_LEN)
    pin.translate(App.Vector(px, py, pz))

    po = DOC.addObject("Part::Feature", f"Pin_{PIN_NAMES[i]}")
    po.Shape = pin
    safe_color(po, (0.9, 0.85, 0.3))

    po.addProperty("App::PropertyString", "PinName", "PinData", "Pin name")
    po.PinName = PIN_NAMES[i]

# ============================
#   HEADER HOUSING
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

hshape = main.fuse(w1).fuse(w2)

hobj = DOC.addObject("Part::Feature", "HeaderHousing")
hobj.Shape = hshape
safe_color(hobj, (0.85, 0.91, 0.05))

# ============================
#   MOUNTING HOLE 4MM (sin pad)
# ============================
MH_DIAM = 4.0
MH_R = MH_DIAM / 2

pin_center_y = py0 + GROUP_LEN / 2
MH_X = EDGE_X + 5.0
MH_Y = pin_center_y

mh = Part.makeCylinder(MH_R, E)
mh.translate(App.Vector(MH_X, MH_Y, 0))
pcb_obj.Shape = pcb_obj.Shape.cut(mh)

# ============================
#   POTENCIOMETRO
# ============================
POT_W = 7.0
POT_L = 7.0
POT_H = 5.0

POT_X = MH_X + 6.5
POT_Y = MH_Y - POT_L/2 - 2.5
POT_Z = E

p = Part.makeBox(POT_W, POT_L, POT_H)
p.translate(App.Vector(POT_X, POT_Y, POT_Z))

pobj = DOC.addObject("Part::Feature", "Potentiometer")
pobj.Shape = p
safe_color(pobj, (0.15, 0.80, 0.85))

# ============================
#   "X" DEL PERILLERO
# ============================

cx = POT_X + POT_W/2
cy = POT_Y + POT_L/2
cz = POT_Z + POT_H/2

AXLE_DIAM = 3.0
AXLE_R = AXLE_DIAM / 2
AXLE_DEPTH = 1       # muesca superficial, no atraviesa todo

SLOT_W = 0.9
SLOT_L = AXLE_DIAM + 0.4
SLOT_D = AXLE_DEPTH

# cara superior del pot
top_z = POT_Z + POT_H

# cilindro de la cavidad
base_hole = Part.makeCylinder(AXLE_R, SLOT_D)
base_hole.translate(App.Vector(cx, cy, top_z - SLOT_D))

# ranura vertical
slot_ns = Part.makeBox(SLOT_L, SLOT_W, SLOT_D)
slot_ns.translate(App.Vector(cx - SLOT_L/2, cy - SLOT_W/2, top_z - SLOT_D))

# ranura horizontal
slot_ew = Part.makeBox(SLOT_W, SLOT_L, SLOT_D)
slot_ew.translate(App.Vector(cx - SLOT_W/2, cy - SLOT_L/2, top_z - SLOT_D))

# unión y corte
x_cut = base_hole.fuse(slot_ns).fuse(slot_ew)
pobj.Shape = pobj.Shape.cut(x_cut)
pobj.purgeTouched()

# ============================
#   COLOR BLANCO PARA LA "X" (relleno superficial)
# ============================

# Hacemos una copia del volumen de corte
fill = x_cut.copy()

# Lo limitamos a una lámina muy fina (0.25 mm) en la base del hueco
# Usa el plano Z del fondo del corte
fill = fill.common(
    Part.makeBox(
        100, 100, 0.25,
        App.Vector(0, 0, top_z - SLOT_D)   # superficie del hueco
    )
)

fill_obj = DOC.addObject("Part::Feature", "X_Fill")
fill_obj.Shape = fill
safe_color(fill_obj, (1.0, 1.0, 1.0))  # blanco


# ============================
#   DIMENSIONES PIN EN L (SONDA)
# ============================
L_PIN_THICK = 0.64        # grosor cuadrado del pin
L_VERTICAL  = 6        # cuanto sube el pin
L_HORIZONTAL = 6        # cuánto sobresale hacia adelante
# ============================
#   PUERTO SUPERIOR (SONDA) – HOLES, PADS, PINES EN L
# ============================
SONDA_PINS = 2
SONDA_PITCH = 2.54
s_px = L - 2.0
s_group = (SONDA_PINS - 1) * SONDA_PITCH
s_py0 = (A - s_group) / 2

# --- holes ---
for i in range(SONDA_PINS):
    cy = s_py0 + i * SONDA_PITCH
    h = Part.makeCylinder(HOLE_R, E)
    h.translate(App.Vector(s_px, cy, 0))
    pcb_obj.Shape = pcb_obj.Shape.cut(h)

# --- pads ---
for i in range(SONDA_PINS):
    cy = s_py0 + i * SONDA_PITCH

    o = Part.makeCylinder(PAD_R, PAD_H)
    ii = Part.makeCylinder(INNER_R, PAD_H)
    ring = o.cut(ii)
    ring.translate(App.Vector(s_px, cy, E))

    pad = DOC.addObject("Part::Feature", f"SondaPad_{i+1}")
    pad.Shape = ring
    safe_color(pad, (0.82, 0.78, 0.66))

# --- pins en L (sin dimensiones negativas)
    # vertical hacia arriba
    vx = s_px - L_PIN_THICK/2
    vy = cy - L_PIN_THICK/2
    vz = E - 3   # partir desde la superficie del PCB

    v = Part.makeBox(L_PIN_THICK, L_PIN_THICK, L_VERTICAL)
    v.translate(App.Vector(vx, vy, vz))

    # horizontal hacia la derecha (en la parte alta)
    hx = vx + L_PIN_THICK - 0.65
    hy = vy
    hz = vz + L_VERTICAL - L_PIN_THICK/2

    h = Part.makeBox(L_HORIZONTAL, L_PIN_THICK, L_PIN_THICK)
    h.translate(App.Vector(hx, hy, hz))


    bent = v.fuse(h)

    pin = DOC.addObject("Part::Feature", f"SondaPin_{i+1}")
    pin.Shape = bent
    safe_color(pin, (0.92, 0.86, 0.32))

# ============================
#   JST-XH HEMBRA 2P – HOUSING (orientado a los pines L)
# ============================

# Dimensiones reales JST-XH 2P
XH_W = 8.1           # ancho (eje Y)
XH_L = 5.8           # profundidad (eje X)
XH_H = 6.3           # altura (eje Z)
XH_WALL = 1.0        # grosor paredes
XH_SLOT_W = 3.4      # ancho de la boca (Y)
XH_SLOT_H = 1.6      # alto (Z)
XH_SLOT_D = 2.2      # profundidad de la boca (X)

# Posición: boca mirando hacia +X (pines horizontales)
xh_x = s_px + L_HORIZONTAL - 5.65    # pega a los pines L
xh_y = s_py0 - (XH_W/2) + (SONDA_PITCH/2)
xh_z = E

# Cuerpo
xh_body = Part.makeBox(XH_L, XH_W, XH_H)
xh_body.translate(App.Vector(xh_x, xh_y, xh_z))

# Cavidad interna (vacío que se abre hacia +X)
inner = Part.makeBox(
    XH_L - XH_WALL,
    XH_W - 2*XH_WALL,
    XH_H - 1.2
)
inner.translate(App.Vector(
    xh_x + XH_WALL,        # cavidad abre hacia adelante (+X)
    xh_y + XH_WALL,
    xh_z + 1.2
))

# Boca frontal (abierta hacia los pines)
slot = Part.makeBox(
    XH_SLOT_D,
    XH_SLOT_W,
    XH_SLOT_H
)
slot.translate(App.Vector(
    xh_x + XH_L - XH_SLOT_D,
    xh_y + (XH_W - XH_SLOT_W)/2,
    xh_z + (XH_H - XH_SLOT_H)/2
))

# Pestañas laterales (izquierda/derecha en Y)
tab_left = Part.makeBox(1.0, 1.6, 2.0)
tab_left.translate(App.Vector(
    xh_x + 2.0,
    xh_y - 1.6,
    xh_z + 2.0
))

tab_right = Part.makeBox(1.0, 1.6, 2.0)
tab_right.translate(App.Vector(
    xh_x + 2.0,
    xh_y + XH_W,
    xh_z + 2.0
))

# Unión final
xh_final = (
    xh_body
    .cut(inner)   # cavidad interna
    .cut(slot)    # boca frontal
    .fuse(tab_left)
    .fuse(tab_right)
)

xh_obj = DOC.addObject("Part::Feature", "JST_XH_2P")
xh_obj.Shape = xh_final
safe_color(xh_obj, (0.92, 0.92, 0.92))


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

print("✔ HD-38 v1.1 generada:")
print("   FCStd:", fcstd_path)
print("   STL :", stl_path)

if GUI:
    try:
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    except:
        pass
