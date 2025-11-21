import FreeCAD as App
import Part
import Import
import os

# ============================
#   TTL-USB BASE: PCB + PINES
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
# PCB
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
# HEADER DE 6 PINES
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

# --- holes + pads + pins ---
for i in range(N_PINS):
    cx = EDGE_X
    cy = py0 + i * PIN_PITCH

    # agujero pasante
    h = Part.makeCylinder(HOLE_R, E)
    h.translate(App.Vector(cx, cy, 0))
    pcb_obj.Shape = pcb_obj.Shape.cut(h)

    # pad superior
    outer = Part.makeCylinder(PAD_R, PAD_H)
    inner = Part.makeCylinder(INNER_R, PAD_H)
    ring = outer.cut(inner)
    ring.translate(App.Vector(cx, cy, E))

    pad = DOC.addObject("Part::Feature", f"Pad_{PIN_NAMES[i]}")
    pad.Shape = ring
    safe_color(pad, (0.80, 0.75, 0.65))

    # pin box
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
# USB-A MALE (cavidad en el frente correcto)
# --------------------------------------

usblen, usbw, usbh = 19, 11, 4
usb_pos = App.Vector(18, 2, 1.6)

# Sólido del USB
usb_solid = Part.makeBox(usblen, usbw, usbh)
usb_solid.translate(usb_pos)

# CAVIDAD: parte desde la cara frontal (X = usb_pos.x + usblen)
cav_len = 12      # profundidad hacia adentro
cav_w   = 10.9       # ancho
cav_h   = 3.8     # alto

# coordenadas relativas dentro del USB
cav_x = usblen - cav_len            # empieza en la boca (lado X+)
cav_y = (usbw - cav_w) / 2
cav_z = (usbh - cav_h) / 2

cavity = Part.makeBox(cav_len, cav_w, cav_h)
cavity.translate(usb_pos + App.Vector(cav_x, cav_y, cav_z))

# aplicar corte
usb_final = usb_solid.cut(cavity)

usb = DOC.addObject("Part::Feature", "USB_A_Male")
usb.Shape = usb_final
safe_color(usb, (0.8,0.8,0.85))

# --------------------------------------
# LENGÜETA BLANCA INTERNA (INSULATOR)
# --------------------------------------

# Dimensiones de la cavidad (ya usadas)
cav_len = 14
cav_w   = 10.8
cav_h   = 3.8

# Lengüeta típica USB-A
tongue_len = cav_len - 2      # un poco más corta que la cavidad
tongue_w   = cav_w   - 1      # un margen pequeño lateral
tongue_h   = cav_h   - 2      # más bajita

# posición: centrada en Y y Z, y un poco adentro desde el frente
tongue_x = usblen - tongue_len - 0.4     # ligeramente retrasada desde la boca
tongue_y = (usbw - tongue_w) / 2
tongue_z = (usbh - tongue_h) / 0.5 - 4.9

tongue_solid = Part.makeBox(tongue_len, tongue_w, tongue_h)
tongue_solid.translate(usb_pos + App.Vector(tongue_x, tongue_y, tongue_z))

tongue = DOC.addObject("Part::Feature", "USB_Tongue")
tongue.Shape = tongue_solid
safe_color(tongue, (0.99, 0.99, 0.99))   # blanco sucio clásico del USB

# --------------------------------------
# CONTACTOS (4 pads lineales)
# --------------------------------------

# típicamente 4 pads en fila, centrados
pad_count = 4
pad_w = tongue_w * 0.1
pad_l = tongue_len * 0.88
pad_h = 0.15
pad_pitch = tongue_w * 0.15   # espaciado entre pads

# inicio en Y para centrarlos
total_width = (pad_count * pad_w) + (pad_pitch * (pad_count - 1))
pad_y0 = (tongue_w - total_width) / 2

for i in range(pad_count):
    px = tongue_x + 0.2                     # cerca del frente de la lengüeta
    py = tongue_y + pad_y0 + i*(pad_w+pad_pitch)
    pz = tongue_z + tongue_h - pad_h + 0.05 # arriba de la lengüeta

    pad = Part.makeBox(pad_l, pad_w, pad_h)
    pad.translate(usb_pos + App.Vector(px, py, pz))

    pad_obj = DOC.addObject("Part::Feature", f"USB_Pad_{i+1}")
    pad_obj.Shape = pad
    safe_color(pad_obj, (0.85, 0.82, 0.55))   # color metalico dorado típico

# --------------------------------------
# HOLES SUPERIORES PARA VER LOS PADS
# --------------------------------------

# dimensiones reales aproximadas
ih_len = 2.0     # largo de la ventana (X)
ih_w   = 2.0     # ancho de la ventana (Y)
ih_h   = 2    # perforación de la chapa (Z)

# separación entre ambas ranuras
ih_gap = 3

# posición longitudinal: centradas sobre la lengüeta interna
ih_x = 12     # desplazar o ajustar según tu insulator
# centrado en ancho del USB
ih_y_center = usbw / 2 

# coordenadas de cada hole
# primer hole
h1 = Part.makeBox(ih_len, ih_w, ih_h)
h1.translate(usb_pos + App.Vector(
    ih_x,
    ih_y_center - ih_w - ih_gap/2,
    usbh - ih_h - 0.2 + 2  # justo sobre la chapa superior
))

# segundo hole
h2 = Part.makeBox(ih_len, ih_w, ih_h)
h2.translate(usb_pos + App.Vector(
    ih_x,
    ih_y_center + ih_gap/2,
    usbh - ih_h - 0.2 + 2
))

# cortar del blindaje
usb.Shape = usb.Shape.cut(h1)
usb.Shape = usb.Shape.cut(h2)


# --------------------------------------
# FINAL
# --------------------------------------
DOC.recompute()

fcstd_path = os.path.join(BUILD_DIR, "ttl_usb_base.FCStd")
stl_path   = os.path.join(BUILD_DIR, "ttl_usb_base.stl")

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
