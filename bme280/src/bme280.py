import FreeCAD as App
import Part
import Import
import os

import Draft

GUI = App.GuiUp
if GUI:
    import FreeCADGui as Gui

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "build"))
os.makedirs(BUILD_DIR, exist_ok=True)

# ============================
#   PARÁMETROS DEL BREAKOUT
# ============================
L = 10.0
A = 13.0
E = 1.6

# Pines
N = 4
P = 2.54
D = 1.2
OFF = 1.4

# Sensor metálico
S_L = 2.0
S_A = 2.0
S_E = 1.0

# Agujero grande
AGUJERO_D = 4.0
BORDE = 0.5
# ============================

# ----------------------------
# Helper: safe view-object setter
# ----------------------------
def safe_set_view(obj, **kwargs):
    """Set attributes on obj.ViewObject if it exists (safe for headless)."""
    vo = getattr(obj, "ViewObject", None)
    if not vo:
        return
    for k, v in kwargs.items():
        try:
            setattr(vo, k, v)
        except Exception:
            # Ignore individual failures to keep script robust
            pass

# ============================

doc = App.newDocument("BME280_Breakout")

# --- Metadata de pinout ---
PIN_NAMES = ["VIN", "GND", "SCL", "SDA"]
pinmeta = doc.addObject("App::FeaturePython", "PinMeta")
pinmeta.addProperty("App::PropertyStringList", "Names", "Pinout", "Pin names")
pinmeta.Names = PIN_NAMES

# ============================
#   CONSTRUCCIÓN COMPLETA
# ============================

# PCB base
pcb = Part.makeBox(L, A, E)

# --- Agujeros de pines ---
total = (N - 1) * P
start_x = (L - total) / 2.0
radio_pin = D / 2.0

for i in range(N):
    x = start_x + i * P
    y = OFF
    hole = Part.makeCylinder(radio_pin, E, App.Vector(x, y, 0))
    pcb = pcb.cut(hole)

# --- Agujero grande con borde metálico ---
radio_aguj = AGUJERO_D / 2.0
radio_ext = radio_aguj + BORDE

aro_x = ((L - (2 * radio_ext)) / 2.0) + 0.5
aro_y = A - radio_ext - 0.6

# Crear bordes metálicos como anillos planos
GROSOR_BORDE = 0.1  # 0.1mm de grosor

# BORDE SUPERIOR (en la cara superior del PCB)
disco_ext_sup = Part.makeCylinder(radio_ext, GROSOR_BORDE, App.Vector(aro_x, aro_y, E))
hueco_int_sup = Part.makeCylinder(radio_aguj, GROSOR_BORDE + 0.1, App.Vector(aro_x, aro_y, E - 0.05))
borde_metalico_sup = disco_ext_sup.cut(hueco_int_sup)

# BORDE INFERIOR (en la cara inferior del PCB)
disco_ext_inf = Part.makeCylinder(radio_ext, GROSOR_BORDE, App.Vector(aro_x, aro_y, -0.1))
hueco_int_inf = Part.makeCylinder(radio_aguj, GROSOR_BORDE + 0.1, App.Vector(aro_x, aro_y, -0.1))
borde_metalico_inf = disco_ext_inf.cut(hueco_int_inf)

# Validar y limpiar las formas
if not borde_metalico_sup.isNull() and len(borde_metalico_sup.Solids) > 0:
    borde_metalico_sup = borde_metalico_sup.removeSplitter()
else:
    print("⚠ Advertencia: Borde metálico superior inválido")

if not borde_metalico_inf.isNull() and len(borde_metalico_inf.Solids) > 0:
    borde_metalico_inf = borde_metalico_inf.removeSplitter()
else:
    print("⚠ Advertencia: Borde metálico inferior inválido")

# Crear el hueco en la PCB (necesario para cortar la PCB)
hueco_pcb = Part.makeCylinder(radio_aguj, E, App.Vector(aro_x, aro_y, 0))
pcb = pcb.cut(hueco_pcb)

# --- Sensor metálico ---
sensor_x = aro_x + radio_ext + 1.5
sensor_y = aro_y - (S_A / 2.0) + 1
sensor_z = E

if sensor_x + S_L > L - 0.5:
    sensor_x = L - S_L - 0.5

if sensor_y + S_A > A - 0.5:
    sensor_y = A - S_A - 0.5

if sensor_y < 0.5:
    sensor_y = 0.5

sensor = Part.makeBox(S_L, S_A, S_E)
sensor.translate(App.Vector(sensor_x, sensor_y, sensor_z))

# ============================
#   PINES FÍSICOS
# ============================

PIN_W = 0.64
PIN_L = 11
PIN_NAMES = ["VIN", "GND", "SCL", "SDA"]

pins_objs = []
for i in range(N):
    x = start_x + i * P
    y = OFF

    # Centrarlos sobre el agujero
    px = x - PIN_W/2
    py = y - PIN_W/2

    # Van hacia abajo del PCB
    pz = -PIN_L + 2

    pin = Part.makeBox(PIN_W, PIN_W, PIN_L)
    pin.translate(App.Vector(px, py, pz))

    obj = doc.addObject("Part::Feature", f"Pin_{PIN_NAMES[i]}")
    obj.Shape = pin

    obj.addProperty("App::PropertyColor", "Color")
    obj.Color = (0.9, 0.85, 0.3)  # doradito

    safe_set_view(obj, ShapeColor=(0.9, 0.85, 0.3))

    pins_objs.append(obj)

# ============================
#   ANILLOS DE SOLDADURA (PADS)
# ============================

PAD_OD = 1.6
PAD_R = PAD_OD / 2
PAD_H = 0.05          # grueso visible del pad

hole_r = D / 2

pads_objs = []
for i in range(N):
    x = start_x + i * P
    y = OFF

    outer = Part.makeCylinder(PAD_R, PAD_H)
    inner = Part.makeCylinder(hole_r, PAD_H + 0.02)

    ring = outer.cut(inner)
    ring.translate(App.Vector(x, y, E))

    obj = doc.addObject("Part::Feature", f"Pad_{PIN_NAMES[i]}")
    obj.Shape = ring

    obj.addProperty("App::PropertyColor", "Color")
    obj.Color = (0.80, 0.75, 0.65)

    safe_set_view(obj, ShapeColor=(0.80, 0.75, 0.65))

    pads_objs.append(obj)

# ============================
#   HOUSING CON ALAS REALES (EJE X)
# ============================

HOUSING_W = 2          # profundidad del bloque (Y)
HOUSING_H = 2          # altura bajo la PCB
MARG = 0.8             # holgura del largo en X

WING_EXTRA = 0.6       # cuánto sobresalen las alas en X

# Largo total del housing (eje X)
group_len = (N - 1) * P
housing_len = group_len + MARG

# Bloque principal: centrado en X respecto a los pines
hx = start_x + group_len/2 - housing_len/2
hy = OFF - HOUSING_W + 1
hz = -HOUSING_H

# --- Cuerpo central ---
body = Part.makeBox(housing_len, HOUSING_W, HOUSING_H)
body.translate(App.Vector(hx, hy, hz))

# --- Alas (en eje X) ---
# Ala izquierda
wing_left = Part.makeBox(WING_EXTRA, HOUSING_W, HOUSING_H)
wing_left.translate(App.Vector(hx - WING_EXTRA, hy, hz))

# Ala derecha
wing_right = Part.makeBox(WING_EXTRA, HOUSING_W, HOUSING_H)
wing_right.translate(App.Vector(hx + housing_len, hy, hz))

# Unión total
housing = body.fuse(wing_left).fuse(wing_right)

housing_obj = doc.addObject("Part::Feature", "HeaderHousing")
housing_obj.Shape = housing

housing_obj.addProperty("App::PropertyColor", "Color")
housing_obj.Color = (0.05, 0.05, 0.05)
safe_set_view(housing_obj, ShapeColor=(0.05, 0.05, 0.05))

# --------------------------------------
# LABELS sobre la PCB (orientadas CCW desde origen)
# --------------------------------------

FONT = "/usr/share/fonts/TTF/DejaVuSans.ttf"

x0 = 9.2
dx = -2.5
y0 = 2.5
dy = -2

labels = [
    ("SDA", "Text_SDA"),
    ("SCL", "Text_SCL"),
    ("GND", "Text_GND"),
    ("VIN", "Text_VIN")
]

for i, (text, name) in enumerate(labels):
    pos = App.Vector(x0 + i*dx, y0, E)

    txt = Draft.makeShapeString(
        String=text,
        FontFile=FONT,
        Size=1,
        Tracking=0
    )

    # placement completo desde origen: posición + rotación CCW 90°
    txt.Placement = App.Placement(
        pos,
        App.Rotation(App.Vector(0,0,1), 90)
    )

    doc.recompute()

    solid = txt.Shape.extrude(App.Vector(0, 0, 0.01))

    obj = doc.addObject("Part::Feature", name)
    obj.Shape = solid

    obj.addProperty("App::PropertyColor", "Color")
    obj.Color = (0.99, 0.99, 0.99)
    safe_set_view(obj, ShapeColor=(0.99, 0.99, 0.99))

doc.recompute()


# ============================
#   CREACIÓN DE OBJETOS
# ============================

pcb_obj = doc.addObject("Part::Feature", "PCB")
borde_sup_obj = doc.addObject("Part::Feature", "BordeMetalicoSuperior")
borde_inf_obj = doc.addObject("Part::Feature", "BordeMetalicoInferior")
sensor_obj = doc.addObject("Part::Feature", "BME280_Sensor")

pcb_obj.Shape = pcb
borde_sup_obj.Shape = borde_metalico_sup
borde_inf_obj.Shape = borde_metalico_inf
sensor_obj.Shape = sensor

# Añadir propiedad de color personalizada para exportación
for obj in [pcb_obj, borde_sup_obj, borde_inf_obj, sensor_obj]:
    obj.addProperty("App::PropertyColor", "Color", "Base", "Object color")

# Definir colores
pcb_color = (0.55, 0.00, 0.45)
borde_color = (0.65, 0.65, 0.65)
sensor_color = (0.75, 0.75, 0.75)

# Asignar colores a la propiedad (siempre)
pcb_obj.Color = pcb_color
borde_sup_obj.Color = borde_color
borde_inf_obj.Color = borde_color
sensor_obj.Color = sensor_color

# Colores visuales (solo si hay GUI) - ahora con safe_set_view
safe_set_view(pcb_obj, ShapeColor=pcb_color)
safe_set_view(borde_sup_obj, ShapeColor=borde_color, DisplayMode="Shaded")
safe_set_view(borde_inf_obj, ShapeColor=borde_color, DisplayMode="Shaded")
safe_set_view(sensor_obj, ShapeColor=sensor_color)


doc.recompute()

# ============================
#   EXPORTACIÓN
# ============================

fcstd_path = os.path.join(BUILD_DIR, "bme280.FCStd")
stl_path   = os.path.join(BUILD_DIR, "bme280.stl")

doc.saveAs(fcstd_path)
Import.export([pcb_obj, borde_sup_obj, borde_inf_obj, sensor_obj], stl_path)

print("✔ BME280 generado:")
print("   FCStd:", fcstd_path)
print("   STL :", stl_path)

if GUI:
    try:
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    except:
        pass
