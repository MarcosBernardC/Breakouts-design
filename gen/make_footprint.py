#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

# -----------------------------
#  Parámetros desde línea de comandos
# -----------------------------
if len(sys.argv) < 2:
    print("Uso: python3 make_footprint.py <holes.json> [output.kicad_mod]")
    print("  Ejemplo: python3 make_footprint.py gen/bme280_holes.json gen/bme280_auto.kicad_mod")
    sys.exit(1)

HOLES_JSON = Path(sys.argv[1]).resolve()
if not HOLES_JSON.exists():
    raise FileNotFoundError(f"No existe {HOLES_JSON}")

# Archivo de salida (opcional)
if len(sys.argv) >= 3:
    OUT_FOOT = Path(sys.argv[2]).resolve()
else:
    # Por defecto: mismo directorio, cambiar extensión
    OUT_FOOT = HOLES_JSON.with_suffix(".kicad_mod")

# -----------------------------
#  Leer datos de agujeros
# -----------------------------
with open(HOLES_JSON, "r") as f:
    data = json.load(f)

pins = data.get("pins", [])

# Verificar si hay pines
if len(pins) == 0:
    print("⚠ No hay pines en el archivo JSON. No se puede generar footprint.")
    print(f"  → {HOLES_JSON}")
    sys.exit(0)

# -----------------------------
#  Generar footprint KiCad
# -----------------------------
# Extraer nombre del módulo desde el nombre del archivo
# Ej: bme280_holes.json -> BME280_auto
module_name = HOLES_JSON.stem.replace("_holes", "").upper()

# KiCad usa mm, perfecto
lines = []
lines.append(f'(footprint "{module_name}_auto" (version 20240115)')
lines.append('  (generator "TARS")')

for i, p in enumerate(pins, start=1):
    name = p.get("name") if p.get("name") else f"PIN{i}"
    x = p["x"]
    y = p["y"]
    d = p["diameter"]

    pad = (
        f'  (pad "{name}" thru_hole circle '
        f'(at {x} {y}) (size {d+0.4} {d+0.4}) (drill {d}) '
        f'(layers "*.Cu" "*.Mask"))'
    )

    lines.append(pad)

lines.append(")")

# -----------------------------
#  Guardar footprint
# -----------------------------
OUT_FOOT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_FOOT, "w") as f:
    f.write("\n".join(lines))

print("✔ Footprint generado:")
print(f"  → {OUT_FOOT}")
print(f"  Pines: {len(pins)}")
