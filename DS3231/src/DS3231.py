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
CR_D = 20.0   # diámetro exterior del portapilas
CR_H = 5.0    # altura total

cr_radius = CR_D / 2
cr_cyl = Part.makeCylinder(cr_radius, CR_H)

# ---- Cavidad interna (donde va la CR2032) ----
CAV_D = 18.5           # diámetro interior
CAV_H = 3.0            # profundidad de la cavidad
cav_radius = CAV_D / 2

inner_cyl = Part.makeCylinder(cav_radius, CAV_H)

# centrar en X/Y y moverla hacia ARRIBA, no hacia abajo
inner_cyl.translate(App.Vector(
    cr_radius - cav_radius,
    cr_radius - cav_radius,
    CR_H - CAV_H  # 👉 cavidad en la parte superior
))

# ---- Boolean cut (resta) ----
cr_with_cavity = cr_cyl.cut(inner_cyl)

# ---- Colocación sobre la PCB ----
cr_x = L/2 
cr_y = A/2 - 2
cr_z = E

cr_with_cavity.translate(App.Vector(cr_x, cr_y, cr_z))

# ---- Crear objeto en FreeCAD ----
cr_obj = doc.addObject("Part::Feature", "CR2032_Holder")
cr_obj.Shape = cr_with_cavity

cr_color = (0.05, 0.05, 0.05)
cr_obj.addProperty("App::PropertyColor", "Color", "Base", "Object color")
cr_obj.Color = cr_color
if GUI:
    cr_obj.ViewObject.ShapeColor = cr_color


# ============================
#   HOLES EN EL LADO ESTRECHO (centrados)
# ============================
HOLE_D = 1.0
HOLE_R = HOLE_D / 2
N_HOLES = 6

EDGE_Y = 2.0          # distancia del borde superior/inferior
HOLE_SPACING = 2.5

# Longitud total del grupo
group_length = (N_HOLES - 1) * HOLE_SPACING

# X inicial para centrar la tira en L = 21 mm
hx0 = (L / 2) - (group_length / 2)

# Y del borde estrecho (aquí en borde superior)
hy = A - EDGE_Y

holes = []
for i in range(N_HOLES):
    hx = hx0 + i * HOLE_SPACING

    hole = Part.makeCylinder(HOLE_R, E)
    hole.translate(App.Vector(hx, hy, 0))

    hole_obj = doc.addObject("Part::Feature", f"Hole_{i+1}")
    hole_obj.Shape = hole
    holes.append(hole_obj)

# Cortar agujeros en la PCB
pcb_cut = pcb_obj.Shape
for h in holes:
    pcb_cut = pcb_cut.cut(h.Shape)

pcb_obj.Shape = pcb_cut

# ============================
#   RECORTE DE ESQUINAS DIAGONALES (triángulos 1x1 mm)
# ============================
CUT = 1.0

# ---- Triángulo esquina izquierda ----
pts_left = [
    App.Vector(0, A, 0),
    App.Vector(CUT, A, 0),
    App.Vector(0, A - CUT, 0)
]
wire_left = Part.makePolygon(pts_left + [pts_left[0]])
face_left = Part.Face(wire_left)
cut_left = face_left.extrude(App.Vector(0, 0, E))

# ---- Triángulo esquina derecha ----
pts_right = [
    App.Vector(L, A, 0),
    App.Vector(L - CUT, A, 0),
    App.Vector(L, A - CUT, 0)
]
wire_right = Part.makePolygon(pts_right + [pts_right[0]])
face_right = Part.Face(wire_right)
cut_right = face_right.extrude(App.Vector(0, 0, E))

# Aplicar recortes
pcb_cut = pcb_obj.Shape.cut(cut_left)
pcb_cut = pcb_cut.cut(cut_right)
pcb_obj.Shape = pcb_cut

# ============================
#   RECOMPUTE
# ============================
doc.recompute()

# ============================
#   EXPORT
# ============================
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
