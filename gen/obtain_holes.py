import FreeCAD as App
import Part
import json
import os
import sys
from pathlib import Path

# -----------------------------
#  Parámetros desde variables de entorno o línea de comandos
# -----------------------------
# freecadcmd procesa todos los argumentos como archivos de proyecto,
# así que usamos variables de entorno como método principal

FCSTD_STR = os.environ.get("FCSTD_FILE")
OUT_STR = os.environ.get("OUT_FILE")

# Si no hay variables de entorno, intentar con sys.argv (para compatibilidad)
if not FCSTD_STR and len(sys.argv) >= 2:
    # Filtrar argumentos que no sean el script actual
    args = [a for a in sys.argv[1:] if a != __file__ and not a.endswith('.py')]
    if args:
        FCSTD_STR = args[0]
        if len(args) >= 2:
            OUT_STR = args[1]

if not FCSTD_STR:
    print("Uso: FCSTD_FILE=<ruta> OUT_FILE=<ruta> freecadcmd obtain_holes.py")
    print("  O: freecadcmd -c \"import os; os.environ['FCSTD_FILE']='<ruta>'; exec(open('gen/obtain_holes.py').read())\"")
    sys.exit(1)

FCSTD = Path(FCSTD_STR).resolve()
if not FCSTD.exists():
    raise FileNotFoundError(f"No existe {FCSTD}")

# Archivo de salida (opcional)
if OUT_STR:
    OUT = Path(OUT_STR).resolve()
else:
    # Por defecto: gen/<nombre_modulo>_holes.json
    BASE = Path(__file__).resolve().parent
    ROOT = BASE.parent
    # Extraer nombre del módulo desde la ruta del FCStd
    # Ej: bme280/build/bme280.FCStd -> bme280
    module_name = FCSTD.parent.parent.name
    OUT = ROOT / "gen" / f"{module_name}_holes.json"

# -----------------------------
#  Cargar documento
# -----------------------------
doc = App.openDocument(str(FCSTD))

# Buscar objeto "PCB" o el primer objeto con Shape
pcb = doc.getObject("PCB")
if pcb is None:
    # Si no hay "PCB", buscar el primer objeto con Shape
    for obj in doc.Objects:
        if hasattr(obj, "Shape") and obj.Shape is not None:
            pcb = obj
            print(f">>> Objeto 'PCB' no encontrado, usando '{obj.Name}' en su lugar.")
            break
    
if pcb is None or not hasattr(pcb, "Shape") or pcb.Shape is None:
    raise RuntimeError("No se encontró ningún objeto con Shape en el archivo FCStd.")

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
OUT.parent.mkdir(parents=True, exist_ok=True)

with OUT.open("w") as f:
    json.dump({"pins": pins, "others": other}, f, indent=4)

# Mensaje informativo
total_holes = len(pins) + len(other)
if total_holes == 0:
    print("⚠ Este sólido no tiene agujeros.")
    print(f"  → {OUT}")
    print("  (Archivo JSON generado con listas vacías)")
else:
    print("✔ Agujeros procesados:")
    print(f"  → {OUT}")
    print(f"  Pins:   {len(pins)}")
    print(f"  Otros:  {len(other)}")
