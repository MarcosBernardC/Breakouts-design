#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# -----------------------------
#  Parámetros desde variables de entorno o línea de comandos
# -----------------------------
# freecadcmd procesa todos los argumentos como archivos de proyecto,
# así que usamos variables de entorno como método principal

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
    print("  O: freecadcmd -c \"import os; os.environ['FCSTD_FILE']='<ruta>'; exec(open('gen/export_wrl.py').read())\"")
    sys.exit(1)

if not OUT_WRL_STR:
    print("❌ ERROR: Se requiere OUT_WRL_FILE")
    sys.exit(1)

# Importar FreeCAD (debe estar dentro del entorno de freecadcmd)
import FreeCAD
import Mesh

# -----------------------------
#  Exportar WRL con colores
# -----------------------------
FCSTD = Path(FCSTD_STR).resolve()
OUT_WRL = Path(OUT_WRL_STR).resolve()

if not FCSTD.exists():
    raise FileNotFoundError(f"No existe {FCSTD}")

print(f">>> Abriendo documento: {FCSTD}")
doc = FreeCAD.openDocument(str(FCSTD))

# Recopilar todos los objetos con shapes válidas
all_objs = []
for o in doc.Objects:
    if hasattr(o, "Shape") and o.Shape is not None and not o.Shape.isNull():
        all_objs.append(o)

if not all_objs:
    print("❌ No hay objetos con shapes válidas para exportar.")
    sys.exit(1)

print(f">>> Procesando {len(all_objs)} objeto(s)...")

# Crear meshes con colores
colored_meshes = []

for o in all_objs:
    print(f"  [+] Mesh: {o.Name}")
    
    # Triangular la shape con precisión adaptativa
    # Para objetos delgados (como anillos), usar mayor precisión
    name_lower = o.Name.lower()
    is_thin = "borde" in name_lower or "metal" in name_lower or "anillo" in name_lower
    
    if is_thin:
        # Para objetos delgados, usar el módulo Mesh directamente
        # que puede generar meshes más densas y robustas
        print(f"    Usando Mesh.fromShape() con alta precisión para objeto delgado")
        try:
            # Mesh.fromShape() genera meshes más densas para objetos delgados
            # Segundo parámetro es la desviación máxima (menor = más preciso)
            msh = Mesh.Mesh()
            msh = Mesh.Mesh(o.Shape.tessellate(0.01))  # Muy alta precisión
            print(f"    Mesh generada: {len(msh.Facets)} facetas")
        except Exception as e:
            print(f"    ⚠ Error con Mesh.fromShape(), usando tessellate: {e}")
            # Fallback a tessellate
            precision = 0.01
            temp = o.Shape.tessellate(precision)
            vertices = temp[0]
            faces = temp[1]
            msh = Mesh.Mesh()
            for f in faces:
                if len(f) >= 3:
                    pts = [vertices[idx] for idx in f[:3]]
                    msh.addFacet(pts[0], pts[1], pts[2])
                    if len(f) > 3:
                        for i in range(3, len(f)):
                            pts_tri = [vertices[f[0]], vertices[f[i-1]], vertices[f[i]]]
                            msh.addFacet(pts_tri[0], pts_tri[1], pts_tri[2])
    else:
        # Para objetos normales, usar precisión estándar
        precision = 0.1
        temp = o.Shape.tessellate(precision)
        vertices = temp[0]
        faces = temp[1]
        msh = Mesh.Mesh()
        for f in faces:
            if len(f) >= 3:
                pts = [vertices[idx] for idx in f[:3]]
                msh.addFacet(pts[0], pts[1], pts[2])
                if len(f) > 3:
                    for i in range(3, len(f)):
                        pts_tri = [vertices[f[0]], vertices[f[i-1]], vertices[f[i]]]
                        msh.addFacet(pts_tri[0], pts_tri[1], pts_tri[2])

    # Obtener color del objeto
    # En modo headless, los colores no se guardan en ViewObject
    # Usamos un mapeo basado en nombres de objetos
    col = None
    name_lower = o.Name.lower()
    
    # Intentar leer desde ViewObject (puede funcionar si el documento se guardó con GUI)
    if hasattr(o, "ViewObject") and o.ViewObject is not None:
        try:
            # En algunos casos, ViewObject puede tener ShapeColor incluso en headless
            if hasattr(o.ViewObject, "ShapeColor"):
                col_tuple = o.ViewObject.ShapeColor
                if col_tuple and len(col_tuple) >= 3:
                    col = tuple(col_tuple[:3])  # RGB
                    print(f"    Color desde ViewObject: {col}")
        except Exception as e:
            pass
    
    # Si no hay color, usar mapeo basado en nombres (coincide con bme280.py)
    if col is None:
        if "pcb" in name_lower:
            col = (0.55, 0.00, 0.45)  # Verde oscuro/magenta para PCB
        elif "borde" in name_lower or "metal" in name_lower:
            col = (0.65, 0.65, 0.65)  # Gris para metal
        elif "sensor" in name_lower or "bme" in name_lower:
            col = (0.75, 0.75, 0.75)  # Gris claro para sensor
        else:
            col = (0.8, 0.8, 0.8)  # Gris por defecto
        print(f"    Color desde mapeo: {col}")

    # Guardar mesh con su color
    colored_meshes.append((msh, col))

# Exportar WRL con colores individuales para cada objeto
# Exportamos cada objeto por separado y los combinamos con sus colores
print(f">>> Exportando a {OUT_WRL}...")
OUT_WRL.parent.mkdir(parents=True, exist_ok=True)

# Mapeo de nombres a colores
name_to_color = {o.Name: col for o, (msh, col) in zip(all_objs, colored_meshes)}

# Exportar cada mesh por separado a archivos temporales
import tempfile
import shutil
import re

temp_dir = Path(tempfile.mkdtemp())
temp_files = []

try:
    for obj_name, (msh, col) in zip([o.Name for o in all_objs], colored_meshes):
        temp_file = temp_dir / f"{obj_name}.wrl"
        try:
            msh.write(str(temp_file))
            temp_files.append((obj_name, temp_file, col))
            print(f"    Exportado {obj_name} temporalmente")
        except Exception as e:
            print(f"    ⚠ Error exportando {obj_name}: {e}")

    # Combinar todos los archivos WRL en uno solo con colores individuales
    print(">>> Combinando objetos con colores individuales...")
    
    # Leer el primer archivo para obtener el header
    if not temp_files:
        raise RuntimeError("No se generaron archivos temporales")
    
    with open(temp_files[0][1], 'r') as f:
        first_content = f.read()
    
    # Extraer el header (hasta el primer Transform)
    header_end = first_content.find("Transform")
    if header_end < 0:
        header_end = first_content.find("Shape")
    if header_end < 0:
        header_end = len(first_content)
    
    header = first_content[:header_end]
    
    # Construir el contenido combinado
    wrl_content = header
    
    # Agregar cada objeto con su material y color
    for obj_name, temp_file, col in temp_files:
        with open(temp_file, 'r') as f:
            obj_content = f.read()
        
        # Extraer el contenido del Transform/Shape
        shape_start = obj_content.find("Transform")
        if shape_start < 0:
            shape_start = obj_content.find("Shape")
        if shape_start < 0:
            continue
        
        # Encontrar el final del Transform (contar llaves)
        brace_count = 0
        shape_end = shape_start
        in_section = False
        for i in range(shape_start, len(obj_content)):
            if obj_content[i] == '{':
                brace_count += 1
                in_section = True
            elif obj_content[i] == '}':
                brace_count -= 1
                if in_section and brace_count == 0:
                    shape_end = i + 1
                    break
        
        shape_section = obj_content[shape_start:shape_end]
        
        # Crear material para este objeto
        r, g, b = col[0], col[1], col[2]
        mat_name = f"Material_{obj_name}"
        material_def = f"""
DEF {mat_name} Material {{
  diffuseColor {r} {g} {b}
  emissiveColor {r*0.3} {g*0.3} {b*0.3}
}}"""
        
        # Insertar el material antes del Transform
        wrl_content += material_def + "\n"
        
        # Modificar el Shape para usar el material
        # Buscar "material Material" y reemplazarlo, o agregarlo si no existe
        if re.search(r'material\s+Material', shape_section, re.IGNORECASE):
            # Reemplazar el material existente
            pattern = r'material\s+Material\s*\{[^}]*\}'
            replacement = f'material USE {mat_name}'
            shape_section = re.sub(pattern, replacement, shape_section, flags=re.IGNORECASE)
        else:
            # Agregar el material después de "appearance Appearance {"
            pattern = r'(appearance\s+Appearance\s*\{)'
            replacement = f'\\1\n        material USE {mat_name}'
            shape_section = re.sub(pattern, replacement, shape_section, flags=re.IGNORECASE)
        
        wrl_content += shape_section + "\n"
        print(f"    Agregado {obj_name} con color RGB({r:.2f}, {g:.2f}, {b:.2f})")
    
    # Guardar el WRL combinado
    with open(OUT_WRL, 'w') as f:
        f.write(wrl_content)
    
finally:
    # Limpiar archivos temporales
    for _, temp_file, _ in temp_files:
        try:
            if temp_file.exists():
                temp_file.unlink()
        except:
            pass
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    except:
        pass

# Cerrar documentos
try:
    FreeCAD.closeDocument(doc.Name)
except Exception as e:
    print(f"⚠ No se pudo cerrar documento: {e}")

print(f"✔ WRL generado: {OUT_WRL}")
