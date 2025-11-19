#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# -----------------------------
#  Parámetros CLI
# -----------------------------
if len(sys.argv) < 2:
    print("Uso: python3 make_footprint.py <holes.json> [basename]")
    sys.exit(1)

HOLES_JSON = Path(sys.argv[1]).resolve()
if not HOLES_JSON.exists():
    raise FileNotFoundError(f"No existe {HOLES_JSON}")

# Basename opcional
if len(sys.argv) >= 3:
    BASENAME = Path(sys.argv[2]).with_suffix("").resolve()
else:
    BASENAME = HOLES_JSON.with_suffix("")

# -----------------------------
#  Leer JSON
# -----------------------------
with open(HOLES_JSON, "r") as f:
    data = json.load(f)

pins = data.get("pins", [])
if not pins:
    print("⚠ No hay pines en el JSON.")
    sys.exit(0)

# -----------------------------
#  Funciones generadoras
# -----------------------------
def make_label_footprint(module_name, pins):
    lines = []
    lines.append(f'(footprint "{module_name}_label" (version 20240115)')
    lines.append('  (generator "TARS")')

    for idx, p in enumerate(pins, start=1):
        name = p.get("name") or f"PIN{idx}"
        x, y, d = p["x"], p["y"], p["diameter"]

        lines.append(
            f'  (pad "{name}" thru_hole circle '
            f'(at {x} {y}) (size {d+0.4} {d+0.4}) (drill {d}) '
            f'(layers "*.Cu" "*.Mask"))'
        )

    lines.append(")")
    return "\n".join(lines)


def make_num_footprint(module_name, pins):
    lines = []
    lines.append(f'(footprint "{module_name}_num" (version 20240115)')
    lines.append('  (generator "TARS")')

    for idx, p in enumerate(pins, start=1):
        pad_name = str(idx)
        x, y, d = p["x"], p["y"], p["diameter"]

        lines.append(
            f'  (pad "{pad_name}" thru_hole circle '
            f'(at {x} {y}) (size {d+0.4} {d+0.4}) (drill {d}) '
            f'(layers "*.Cu" "*.Mask"))'
        )

    lines.append(")")
    return "\n".join(lines)


# -----------------------------
#  Preparar nombres
# -----------------------------
module_name = HOLES_JSON.stem.replace("_holes", "").upper()

LABEL_OUT = BASENAME.with_name(BASENAME.name + "_label.kicad_mod")
NUM_OUT   = BASENAME.with_name(BASENAME.name + "_num.kicad_mod")

LABEL_OUT.parent.mkdir(parents=True, exist_ok=True)
NUM_OUT.parent.mkdir(parents=True, exist_ok=True)

# -----------------------------
#  Guardar ambos footprints
# -----------------------------
with open(LABEL_OUT, "w") as f:
    f.write(make_label_footprint(module_name, pins))

with open(NUM_OUT, "w") as f:
    f.write(make_num_footprint(module_name, pins))

print("✔ Footprints generados:")
print(f"  → {LABEL_OUT}")
print(f"  → {NUM_OUT}")
print(f"  Pines: {len(pins)}")
