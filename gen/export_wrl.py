import sys
import os
from pathlib import Path

# -----------------------------
#  Parámetros desde variables de entorno o línea de comandos
# -----------------------------
FCSTD_STR = os.environ.get("FCSTD_FILE")
OUT_WRL_STR = os.environ.get("OUT_WRL_FILE")

# Si no hay variables de entorno, intentar con sys.argv (para compatibilidad)
if not FCSTD_STR and len(sys.argv) >= 2:
    # Filtrar argumentos que no sean el script actual
    args = [a for a in sys.argv[1:] if a != __file__ and not a.endswith('.py') and a != '--']
    if args:
        FCSTD_STR = args[0]
        if len(args) >= 2:
            OUT_WRL_STR = args[1]

if not FCSTD_STR:
    print("Uso: FCSTD_FILE=<ruta> OUT_WRL_FILE=<ruta> freecadcmd export_wrl.py")
    sys.exit(1)

if not OUT_WRL_STR:
    print("❌ ERROR: Se requiere OUT_WRL_FILE")
    sys.exit(1)

# Importar FreeCAD
import FreeCAD
import Import

# -----------------------------
#  Exportar WRL
# -----------------------------
FCSTD = Path(FCSTD_STR).resolve()
OUT_WRL = Path(OUT_WRL_STR).resolve()

if not FCSTD.exists():
    raise FileNotFoundError(f"No existe {FCSTD}")

print(f">>> Abriendo documento: {FCSTD}")
doc = FreeCAD.openDocument(str(FCSTD))

# Recopilar todos los objetos con shapes válidas
valid_objs = [
    obj for obj in doc.Objects
    if hasattr(obj, "Shape") and obj.Shape is not None and not obj.Shape.isNull()
]

if not valid_objs:
    print("❌ No hay objetos con shapes válidas para exportar.")
    sys.exit(1)

print(f">>> Exportando {len(valid_objs)} objeto(s) a {OUT_WRL}...")
OUT_WRL.parent.mkdir(parents=True, exist_ok=True)

# Convertir a mallas para exportar a VRML
import Mesh
mesh_objs = []
for obj in valid_objs:
    try:
        # Crear objeto malla temporal
        mesh_name = f"{obj.Name}_Mesh"
        mesh_obj = doc.addObject("Mesh::Feature", mesh_name)
        
        # Tessellate (0.1mm de tolerancia es un buen balance para visualización)
        m = Mesh.Mesh()
        m.addFacets(obj.Shape.tessellate(0.1))
        mesh_obj.Mesh = m
        
        # Copiar color si es posible (opcional, pero útil)
        if hasattr(obj, "ViewObject") and hasattr(mesh_obj, "ViewObject"):
             # En headless ViewObject puede no estar completamente disponible o ser limitado
             pass
             
        mesh_objs.append(mesh_obj)
    except Exception as e:
        print(f"⚠ Error al mallar {obj.Name}: {e}")

if not mesh_objs:
    print("❌ No se pudieron generar mallas para exportar.")
    sys.exit(1)

# Exportar a VRML usando Mesh.export
Mesh.export(mesh_objs, str(OUT_WRL))

# Cierre compatible con freecadcmd
try:
    FreeCAD.closeDocument(doc.Name)
except Exception as e:
    print(f"⚠ No se pudo cerrar documento: {e}")

print(f"✔ WRL generado: {OUT_WRL}")
