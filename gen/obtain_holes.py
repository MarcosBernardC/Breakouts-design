import FreeCAD as App
import Part
import json
import os
from pathlib import Path

# -----------------------------
#  Rutas
# -----------------------------
BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
BUILD = ROOT / "bme280" / "build"

FCSTD = BUILD / "bme280.FCStd"
if not FCSTD.exists():
    raise FileNotFoundError(f"No existe {FCSTD}")

# -----------------------------
#  Cargar documento
# -----------------------------
doc = App.openDocument(str(FCSTD))

pcb = doc.getObject("PCB")
if pcb is None:
    raise RuntimeError("No se encontró el objeto 'PCB' en el archivo FCStd.")

shape = pcb.Shape

pins = []
other = []

MAX_PIN_DIAM = 2.0  # regla electrónica estándar

# -----------------------------
#  Extraer cilindros
# -----------------------------
for face in shape.Faces:
    surf = face.Surface
    if surf.__class__.__name__ != "Cylinder":
        continue

    r = surf.Radius
    d = round(2*r, 3)
    cx, cy, cz = surf.Center.x, surf.Center.y, surf.Center.z

    hole = {
        "x": round(cx, 3),
        "y": round(cy, 3),
        "z": round(cz, 3),
        "diameter": d
    }

    # Clasificación automática
    if d <= MAX_PIN_DIAM:
        pins.append(hole)
    else:
        other.append(hole)

# ordenar pines por X (header estándar)
pins.sort(key=lambda h: h["x"])

# -----------------------------
#  Nombres desde metadata
# -----------------------------
meta = doc.getObject("PinMeta")
names = list(meta.Names) if meta else []

for i, hole in enumerate(pins):
    hole["name"] = names[i] if i < len(names) else None

# -----------------------------
#  Exportar
# -----------------------------
OUT = ROOT / "gen" / "holes.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

with OUT.open("w") as f:
    json.dump({"pins": pins, "others": other}, f, indent=4)

print("✔ Agujeros procesados:")
print(f"  → {OUT}")
print(f"  Pins:   {len(pins)}")
print(f"  Otros:  {len(other)}  (ignorados)")  # para tu tranquilidad electrónica
