import FreeCAD as App
import Part
import Import
import os

# Detectar si hay GUI
GUI = App.GuiUp
if GUI:
    import FreeCADGui as Gui

# ============================
#   CONFIGuración
# ============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "build"))
os.makedirs(BUILD_DIR, exist_ok=True)

# ============================
#   PARÁMETROS PCB
# ============================
L = 21.0   # largo
A = 36.0   # ancho
E = 1      # espesor

# ============================
#   DOCUMENTO
# ============================
doc = App.newDocument("DS3231_PCB")

# ============================
#   PCB (solo el bloque)
# ============================
pcb = Part.makeBox(L, A, E)

pcb_obj = doc.addObject("Part::Feature", "PCB")
pcb_obj.Shape = pcb

pcb_color = (0.1, 0.3, 0.9)
pcb_obj.addProperty("App::PropertyColor", "Color", "Base", "Object color")
pcb_obj.Color = pcb_color
if GUI:
    pcb_obj.ViewObject.ShapeColor = pcb_color

# ============================
#   PORTAPILAS (cilindro + cavidad)
# ============================
CR_D = 20.0   # diámetro exterior
CR_H = 5.0    # altura

cr_radius = CR_D / 2
cr_cyl = Part.makeCylinder(cr_radius, CR_H)

# Cavidad interna
CAV_D = 18.5
CAV_H = 3.0
cav_radius = CAV_D / 2

inner_cyl = Part.makeCylinder(cav_radius, CAV_H)
inner_cyl.translate(App.Vector(
    cr_radius - cav_radius,
    cr_radius - cav_radius,
    CR_H - CAV_H
))

cr_with_cavity = cr_cyl.cut(inner_cyl)

# Posicionar portapilas
cr_x = L/2
cr_y = A/2 - 2
cr_z = E
cr_with_cavity.translate(App.Vector(cr_x, cr_y, cr_z))

cr_obj = doc.addObject("Part::Feature", "CR2032_Holder")
cr_obj.Shape = cr_with_cavity

cr_color = (0.05, 0.05, 0.05)
cr_obj.addProperty("App::PropertyColor", "Color", "Base", "Object color")
cr_obj.Color = cr_color
if GUI:
    cr_obj.ViewObject.ShapeColor = cr_color

# ============================
#   HOLES EN EL LADO ESTRECHO
# ============================
HOLE_D = 1.0
HOLE_R = HOLE_D / 2
N_HOLES = 6
EDGE_Y = 2.0
HOLE_SPACING = 2.5

group_length = (N_HOLES - 1) * HOLE_SPACING
hx0 = (L / 2) - (group_length / 2)
hy = A - EDGE_Y

pcb_cut = pcb_obj.Shape

for i in range(N_HOLES):
    hx = hx0 + i * HOLE_SPACING
    hole = Part.makeCylinder(HOLE_R, E)
    hole.translate(App.Vector(hx, hy, 0))
    pcb_cut = pcb_cut.cut(hole)

pcb_obj.Shape = pcb_cut

# ============================
#   RECORTE DE ESQUINAS 1×1 mm
# ============================
CUT = 1.0

pts_left = [
    App.Vector(0, A, 0),
    App.Vector(CUT, A, 0),
    App.Vector(0, A - CUT, 0)
]
cut_left = Part.Face(Part.makePolygon(pts_left + [pts_left[0]])).extrude(App.Vector(0, 0, E))

pts_right = [
    App.Vector(L, A, 0),
    App.Vector(L - CUT, A, 0),
    App.Vector(L, A - CUT, 0)
]
cut_right = Part.Face(Part.makePolygon(pts_right + [pts_right[0]])).extrude(App.Vector(0, 0, E))

pcb_obj.Shape = pcb_obj.Shape.cut(cut_left).cut(cut_right)

# ============================
#   PINES SUELTOS (6 PINES)
# ============================

PIN_SIZE = 0.64        # sección cuadrada
PIN_LEN  = 11.0        # largo total

pin_objs = []

for i in range(N_HOLES):
    # coordenadas X/Y exactas de cada agujero
    hx = hx0 + i * HOLE_SPACING
    hy = A - EDGE_Y

    # posición del pin
    px = hx - PIN_SIZE/2
    py = hy - PIN_SIZE/2
    pz = - (PIN_LEN - E - 1.5)      # casi todo el pin por debajo de la PCB

    # crear pin
    pin = Part.makeBox(PIN_SIZE, PIN_SIZE, PIN_LEN)
    pin.translate(App.Vector(px, py, pz))

    # añadir al documento
    p_obj = doc.addObject("Part::Feature", f"Pin_{i+1}")
    p_obj.Shape = pin
    p_obj.ViewObject.ShapeColor = (0.9, 0.85, 0.3)  # doradito
    pin_objs.append(p_obj)

# ============================
#   HOUSING REALISTA 1x6 (con paredes laterales más gruesas)
# ============================

PIN_PITCH = 2.54
PIN_CLEAR = 0.06
PIN_HOLE = PIN_SIZE + PIN_CLEAR

HOUSING_H = 2.5       # altura del plástico
HOUSING_W = 2.5       # ancho
WALL_X_EXTRA = 0.6    # grosor adicional en cada extremo

# Nuevo largo = largo original + extra en ambos lados
HOUSING_L = WALL_X_EXTRA*2 + (N_HOLES - 1)*PIN_PITCH + PIN_HOLE

# Crear el bloque externo con las paredes más gruesas
housing = Part.makeBox(HOUSING_L, HOUSING_W, HOUSING_H)

# Posicionarlo debajo de la PCB (centrado como antes)
hx_center = hx0 + group_length / 2
housing_x = hx_center - (HOUSING_L / 2)
housing_y = hy - (HOUSING_W / 2)
housing_z = -HOUSING_H

housing.translate(App.Vector(housing_x, housing_y, housing_z))

# ----------------------------
#   Agujeros internos (rectangulares)
# ----------------------------
holes_for_housing = []

for i in range(N_HOLES):

    # La posición global del pin NO cambia
    hx_pin = hx0 + i * HOLE_SPACING

    # Pero ahora el housing creció hacia ambos lados,
    # así que restamos WALL_X_EXTRA para que queden centrados
    hole_x = hx_pin - PIN_HOLE/2 - housing_x + (-WALL_X_EXTRA)
    hole_y = hy - PIN_HOLE/2 - housing_y

    hole_box = Part.makeBox(PIN_HOLE, PIN_HOLE, HOUSING_H)
    hole_box.translate(App.Vector(hole_x, hole_y, 0))

    holes_for_housing.append(hole_box)

# Resta final
housing_real = housing
for h in holes_for_housing:
    housing_real = housing_real.cut(h)

# Añadir al documento
housing_obj = doc.addObject("Part::Feature", "Pin_Header_Housing")
housing_obj.Shape = housing_real
housing_obj.ViewObject.ShapeColor = (0.05, 0.05, 0.05)

# ============================
#   ANILLOS DE SOLDADURA (CENTRADOS)
# ============================

PAD_OD = 1.6
PAD_R  = PAD_OD / 2
PAD_H  = 0.05

INNER_D = HOLE_D
INNER_R = INNER_D / 2

pads_objs = []

for i in range(N_HOLES):
    hx = hx0 + i * HOLE_SPACING
    hy = A - EDGE_Y

    # crear cilindros centrados
    outer = Part.makeCylinder(PAD_R, PAD_H)
    inner = Part.makeCylinder(INNER_R, PAD_H)

    # anillo: outer - inner
    ring = outer.cut(inner)

    # mover el anillo a su posición exacta
    ring.translate(App.Vector(
        hx,     # centro exacto del agujero
        hy,
        E       # sobre la PCB
    ))

    pad_obj = doc.addObject("Part::Feature", f"Pad_{i+1}")
    pad_obj.Shape = ring
    pad_obj.ViewObject.ShapeColor = (0.9, 0.45, 0.1)
    pads_objs.append(pad_obj)

# ============================
#   PILA CR2032 (modo seguro)
# ============================

BAT_D = 19.0
BAT_R = BAT_D / 2
BAT_H = 3.2

battery = Part.makeCylinder(BAT_R, BAT_H)

# posición (misma lógica)
bx = housing_x + HOUSING_L/2
by = housing_y - HOUSING_W - 14
bz = -HOUSING_H + 5

battery.translate(App.Vector(bx, by, bz))

bat_obj = doc.addObject("Part::Feature", "Battery_CR2032")
bat_obj.Shape = battery
bat_obj.ViewObject.ShapeColor = (0.7, 0.7, 0.7)



# ============================
#   RECOMPUTE Y EXPORT
# ============================
doc.recompute()

objects = [pcb_obj, cr_obj]

fcstd_path = os.path.join(BUILD_DIR, "DS3231.FCStd")
stl_path   = os.path.join(BUILD_DIR, "DS3231.stl")

doc.saveAs(fcstd_path)
Import.export(objects, stl_path)

print("✔ PCB + Portapilas del DS3231 generados:")
print("   FCStd:", fcstd_path)
print("   STL :", stl_path)

if GUI:
    try:
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    except:
        pass
