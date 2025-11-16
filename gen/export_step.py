import sys
import os
from pathlib import Path

# -----------------------------
#  Parámetros desde variables de entorno o línea de comandos
# -----------------------------
# freecadcmd procesa todos los argumentos como archivos de proyecto,
# así que usamos variables de entorno como método principal

FCSTD_STR = os.environ.get("FCSTD_FILE")
OUT_STEP_STR = os.environ.get("OUT_STEP_FILE")

# Si no hay variables de entorno, intentar con sys.argv (para compatibilidad)
if not FCSTD_STR and len(sys.argv) >= 2:
    # Filtrar argumentos que no sean el script actual
    args = [a for a in sys.argv[1:] if a != __file__ and not a.endswith('.py') and a != '--']
    if args:
        FCSTD_STR = args[0]
        if len(args) >= 2:
            OUT_STEP_STR = args[1]

if not FCSTD_STR:
    print("Uso: FCSTD_FILE=<ruta> OUT_STEP_FILE=<ruta> freecadcmd export_step.py")
    print("  O: freecadcmd -c \"import os; os.environ['FCSTD_FILE']='<ruta>'; exec(open('gen/export_step.py').read())\"")
    sys.exit(1)

if not OUT_STEP_STR:
    print("❌ ERROR: Se requiere OUT_STEP_FILE")
    sys.exit(1)

# Importar FreeCAD (debe estar dentro del entorno de freecadcmd)
import FreeCAD
import Import

# -----------------------------
#  Exportar STEP
# -----------------------------
FCSTD = Path(FCSTD_STR).resolve()
OUT_STEP = Path(OUT_STEP_STR).resolve()

if not FCSTD.exists():
    raise FileNotFoundError(f"No existe {FCSTD}")

print(f">>> Abriendo documento: {FCSTD}")
doc = FreeCAD.openDocument(str(FCSTD))

# Recopilar todos los objetos con shapes válidas (no nulas)
objs = [
    obj for obj in doc.Objects
    if hasattr(obj, "Shape") and obj.Shape is not None and not obj.Shape.isNull()
]

if not objs:
    print("❌ No hay objetos con shapes válidas para exportar.")
    sys.exit(1)

print(f">>> Exportando {len(objs)} objeto(s) a {OUT_STEP}...")
OUT_STEP.parent.mkdir(parents=True, exist_ok=True)
# Usar Import.export para exportar objetos completos (genera STEP más completo)
Import.export(objs, str(OUT_STEP))

# Cierre compatible con freecadcmd
try:
    FreeCAD.closeDocument(doc.Name)
except Exception as e:
    print(f"⚠ No se pudo cerrar documento: {e}")

print(f"✔ STEP generado: {OUT_STEP}")
