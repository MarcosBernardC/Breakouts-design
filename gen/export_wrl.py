import sys
import os
from pathlib import Path
import tempfile
import re

# -----------------------------
#  Parámetros
# -----------------------------
FCSTD_STR = os.environ.get("FCSTD_FILE")
OUT_WRL_STR = os.environ.get("OUT_WRL_FILE")

if not FCSTD_STR or not OUT_WRL_STR:
    print("Uso: FCSTD_FILE=<ruta> OUT_WRL_FILE=<ruta> freecadcmd export_wrl.py")
    sys.exit(1)

import FreeCAD
import Import
import Mesh

# -----------------------------
#  Funciones
# -----------------------------
def get_color(obj):
    """Obtiene el color del objeto (r, g, b) desde propiedad Color o defecto."""
    if hasattr(obj, "Color"):
        # App::PropertyColor devuelve una tupla (r, g, b, a) o similar
        c = obj.Color
        if len(c) >= 3:
            return (c[0], c[1], c[2])
    return (0.8, 0.8, 0.8) # Default grey

def inject_color(wrl_content, color):
    """Reemplaza el color difuso en el contenido VRML."""
    r, g, b = color
    # Patrón para encontrar diffuseColor
    # VRML: diffuseColor 0.8 0.8 0.8
    pattern = r"diffuseColor\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+"
    replacement = f"diffuseColor {r:.3f} {g:.3f} {b:.3f}"
    return re.sub(pattern, replacement, wrl_content)

# -----------------------------
#  Main
# -----------------------------
FCSTD = Path(FCSTD_STR).resolve()
OUT_WRL = Path(OUT_WRL_STR).resolve()

if not FCSTD.exists():
    raise FileNotFoundError(f"No existe {FCSTD}")

print(f">>> Abriendo documento: {FCSTD}")
doc = FreeCAD.openDocument(str(FCSTD))

valid_objs = [
    obj for obj in doc.Objects
    if hasattr(obj, "Shape") and obj.Shape is not None and not obj.Shape.isNull()
]

if not valid_objs:
    print("❌ No hay objetos con shapes válidas para exportar.")
    sys.exit(1)

print(f">>> Exportando {len(valid_objs)} objeto(s) a {OUT_WRL} con colores...")
OUT_WRL.parent.mkdir(parents=True, exist_ok=True)

final_wrl_content = ["#VRML V2.0 utf8\n"]

with tempfile.TemporaryDirectory() as tmpdirname:
    tmp_dir = Path(tmpdirname)
    
    for i, obj in enumerate(valid_objs):
        try:
            # 1. Crear malla temporal
            mesh_name = f"TempMesh_{i}"
            mesh_obj = doc.addObject("Mesh::Feature", mesh_name)
            m = Mesh.Mesh()
            m.addFacets(obj.Shape.tessellate(0.1))
            mesh_obj.Mesh = m
            
            # 2. Exportar a archivo temporal
            tmp_file = tmp_dir / f"{i}.wrl"
            Mesh.export([mesh_obj], str(tmp_file))
            
            # 3. Leer contenido y procesar
            with open(tmp_file, "r") as f:
                content = f.read()
            
            # Quitar header si existe
            content = content.replace("#VRML V2.0 utf8", "")
            
            # 4. Inyectar color
            color = get_color(obj)
            content = inject_color(content, color)
            
            final_wrl_content.append(f"\n# Object: {obj.Name}\n")
            final_wrl_content.append(content)
            
            # Limpieza objeto temporal
            doc.removeObject(mesh_name)
            
        except Exception as e:
            print(f"⚠ Error procesando {obj.Name}: {e}")

# Escribir archivo final
with open(OUT_WRL, "w") as f:
    f.write("".join(final_wrl_content))

try:
    FreeCAD.closeDocument(doc.Name)
except Exception as e:
    print(f"⚠ No se pudo cerrar documento: {e}")

print(f"✔ WRL generado con colores: {OUT_WRL}")
