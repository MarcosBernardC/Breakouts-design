import FreeCAD as App
import Part
import Import
import os

# GUI opcional
try:
    import FreeCADGui as Gui
    GUI = True
except:
    GUI = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "build"))
os.makedirs(BUILD_DIR, exist_ok=True)

# ============================
#   PARÁMETROS DEL BREAKOUT
# ============================
L = 10.0
A = 12.0
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

doc = App.newDocument("BME280_Breakout")

# --- PCB base ---
pcb = Part.makeBox(L, A, E)

# --- Agujeros ---
total = (N - 1) * P
start_x = (L - total) / 2.0
radio_pin = D / 2.0

for i in range(N):
    x = start_x + i * P
    y = OFF
    hole = Part.makeCylinder(radio_pin, E, App.Vector(x, y, 0))
    pcb = pcb.cut(hole)

pcb_obj = doc.addObject("Part::Feature", "PCB")
pcb_obj.Shape = pcb

if GUI:
    pcb_obj.ViewObject.ShapeColor = (0.55, 0.00, 0.45)

# --- Agujero grande con borde metálico ---
radio_aguj = AGUJERO_D / 2.0
radio_ext = radio_aguj + BORDE

aro_x = ((L - (2 * radio_ext)) / 2.0) + 0.5
aro_y = A - radio_ext - 0.6
aro_z = 0

anillo = Part.makeCylinder(radio_ext, E, App.Vector(aro_x, aro_y, aro_z))
hueco  = Part.makeCylinder(radio_aguj, E, App.Vector(aro_x, aro_y, aro_z))
borde_metalico = anillo.cut(hueco)

pcb = pcb.cut(hueco)
pcb = pcb.fuse(borde_metalico)

pcb_obj.Shape = pcb

# --- Sensor metálico ---
aro_cx = aro_x
aro_cy = aro_y

sensor_x = aro_cx + radio_ext + 1.5
sensor_y = aro_cy - (S_A / 2.0) + 1
sensor_z = E

if sensor_x + S_L > L - 0.5:
    sensor_x = L - S_L - 0.5

if sensor_y + S_A > A - 0.5:
    sensor_y = A - S_A - 0.5

if sensor_y < 0.5:
    sensor_y = 0.5

sensor = Part.makeBox(S_L, S_A, S_E)
sensor.translate(App.Vector(sensor_x, sensor_y, sensor_z))

sensor_obj = doc.addObject("Part::Feature", "BME280_Sensor")
sensor_obj.Shape = sensor

if GUI:
    sensor_obj.ViewObject.ShapeColor = (0.75, 0.75, 0.75)

# --- Final ---
doc.recompute()

# Guardar
fcstd_path = os.path.join(BUILD_DIR, "bme280.FCStd")
stl_path   = os.path.join(BUILD_DIR, "bme280.stl")

doc.saveAs(fcstd_path)
Import.export([sensor_obj], stl_path)

print("✔ BME280 generado:")
print("   FCStd:", fcstd_path)
print("   STL :", stl_path)

# Vista opcional
if GUI:
    try:
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    except:
        pass
