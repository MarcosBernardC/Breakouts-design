import FreeCAD as App
import Part
import Import
import os

# === Resolver rutas ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "build"))
os.makedirs(BUILD_DIR, exist_ok=True)

# --- Crear documento ---
doc = App.newDocument("TestCLI")

# --- Hacer sólido ---
cube = Part.makeBox(10, 10, 10)
# Usar "PCB" como nombre para compatibilidad con obtain_holes.py
obj = doc.addObject("Part::Feature", "PCB")
obj.Shape = cube

# --- Registrar documento (CRÍTICO en CLI) ---
App.setActiveDocument(doc.Name)
App.ActiveDocument = doc

# --- Recompute ---
doc.recompute()

# --- Guardar FCStd ---
# Usar el nombre del módulo (test) para el archivo FCStd
module_name = os.path.basename(os.path.dirname(BASE_DIR))
fcstd_path = os.path.join(BUILD_DIR, f"{module_name}.FCStd")
print("Guardando FCStd en:", fcstd_path)
doc.saveAs(fcstd_path)

# --- Exportar STL ---
stl_path = os.path.join(BUILD_DIR, "cubo.stl")
print("Exportando STL en:", stl_path)
Import.export([obj], stl_path)

print("✔ Completado correctamente.")
