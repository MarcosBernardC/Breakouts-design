#!/usr/bin/env python3
# debug_fcstd.py
# Ejecutar con: freecadpy gen/debug_fcstd.py

import FreeCAD as App
import Part
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
FCSTD = ROOT / "bme280" / "build" / "bme280.FCStd"
OUTDIR = BASE / "debug_out"
OUTDIR.mkdir(parents=True, exist_ok=True)

def info(*msg):
    print(" ".join(str(m) for m in msg))


if not FCSTD.exists():
    print("ERROR: no existe el FCStd:", FCSTD)
    sys.exit(1)

info("Abriendo documento: " + str(FCSTD))
doc = App.openDocument(str(FCSTD))

info("Objetos en el documento:")
for obj in doc.Objects:
    name = obj.Name
    typeid = getattr(obj, "TypeId", "<no TypeId>")
    has_shape = hasattr(obj, "Shape") and obj.Shape is not None
    info(f" - {name:20s}  type: {typeid:25s}  has_shape: {has_shape}")
    if has_shape:
        shape = obj.Shape
        # propiedades de la forma
        try:
            isnull = shape.isNull()
        except Exception:
            isnull = "<error>"
        try:
            nverts = len(shape.Vertexes)
            nedges = len(shape.Edges)
            nfaces = len(shape.Faces)
            nsolids = len(shape.Solids)
        except Exception as e:
            nverts = nedges = nfaces = nsolids = f"err:{e}"
        info(f"    isNull: {isnull}, verts:{nverts}, edges:{nedges}, faces:{nfaces}, solids:{nsolids}")

        # intentar calcular volumen si hay sólidos
        try:
            vol = 0.0
            for s in shape.Solids:
                vol += s.Volume
            info(f"    volumen total (sum solids): {vol:.6f}")
        except Exception as e:
            info(f"    volumen: error ({e})")

        # exportar cada objeto individual como STEP para revisar en otro visor
        step_path = OUTDIR / f"{name}.step"
        try:
            Part.export([obj], str(step_path))
            info(f"    Exportado STEP -> {step_path}")
        except Exception as e:
            info(f"    No se pudo exportar STEP: {e}")

info("\nLista completa de vistas (ViewObjects) disponibles (si hay GUI):")
try:
    guimode = App.GuiUp
    info(" GUI activo: " + str(guimode))
    if guimode:
        # imprimo ViewObject presence
        for obj in doc.Objects:
            vo = getattr(obj, "ViewObject", None)
            info(f" - {obj.Name:20s}  ViewObject: {type(vo).__name__ if vo is not None else 'None'}")
except Exception as e:
    info("Error comprobando GUI/ViewObject: " + str(e))

info("\nArchivos del build dir:")
for p in sorted((ROOT / "bme280" / "build").glob("*")):
    info(" - " + str(p))

info("\nPrueba final: exportar COMBINADO (PCB+sensor+borde) a debug_out/combined.step")
try:
    objs = [o for o in doc.Objects if hasattr(o, "Shape")]
    Part.export(objs, str(OUTDIR / "combined.step"))
    info("  Exportado combined.step")
except Exception as e:
    info("  No se pudo exportar combined.step: " + str(e))

info("\nDEBUG completo. Revisa la carpeta:", str(OUTDIR))
