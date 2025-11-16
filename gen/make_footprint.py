#!/usr/bin/env python3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOLES_JSON = os.path.join(BASE_DIR, "holes.json")
OUT_FOOT = os.path.join(BASE_DIR, "bme280_auto.kicad_mod")

with open(HOLES_JSON, "r") as f:
    data = json.load(f)

pins = data["pins"]

# KiCad usa mm, perfecto
lines = []
lines.append('(footprint "BME280_auto" (version 20240115)')
lines.append('  (generator "TARS")')

for i, p in enumerate(pins, start=1):
    name = p["name"] if p["name"] else f"PIN{i}"
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

with open(OUT_FOOT, "w") as f:
    f.write("\n".join(lines))

print("✔ Footprint generado:")
print("  →", OUT_FOOT)
