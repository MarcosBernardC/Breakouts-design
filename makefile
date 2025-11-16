# ======================================
#   CONFIG
# ======================================
PYTHON_HEADLESS = freecadcmd
PYTHON_GUI      = freecad

# Detectar carpetas que tienen src/, normalizando sin slash final
MODULE_DIRS := $(patsubst %/,%,$(dir $(wildcard */src)))

# Detectar módulos con .py suelto en raíz
ROOT_PYS := $(basename $(notdir $(wildcard *.py)))

# Lista de módulos reales
MODULES := $(MODULE_DIRS) $(ROOT_PYS)

# Targets GUI generados automáticamente: bme280 → bme280_gui
MODULES_GUI := $(addsuffix _gui,$(MODULES))

.PHONY: $(MODULES) $(MODULES_GUI) help holes footprint


# ======================================
#   HELP
# ======================================
help:
	@echo "Uso:"
	@echo "  make <modulo>        - Ejecutar headless (freecadcmd)"
	@echo "  make <modulo>_gui    - Ejecutar con GUI (freecad)"
	@echo
	@echo "Modulos disponibles:"
	@for m in $(MODULES); do echo "  - $$m"; done


# ======================================
#   CREAR ESTRUCTURA STÁNDAR
# ======================================
define ENSURE_STRUCTURE
	@mkdir -p $(1)/src
	@mkdir -p $(1)/build
	@if [ -f $(1).py ]; then \
		echo ">>> Detectado archivo suelto: $(1).py"; \
		echo ">>> Moviendo a $(1)/src/$(1).py"; \
		mv $(1).py $(1)/src/$(1).py; \
	fi
endef


# ======================================
#   HEADLESS (freecadcmd)
# ======================================
$(MODULES):
	@echo ">>> Verificando módulo '$@'..."
	$(call ENSURE_STRUCTURE,$@)
	@if [ ! -f $@/src/$@.py ]; then \
		echo "ERROR: No existe $@/src/$@.py"; \
		exit 1; \
	fi
	@echo ">>> Ejecutando '$@' (modo headless)..."
	$(PYTHON_HEADLESS) $@/src/$@.py
	@echo "✔ Listo."


# ======================================
#   GUI (freecad)
# ======================================
$(MODULES_GUI):
	$(eval mod := $(subst _gui,,$@))

	@echo ">>> Verificando módulo '$(mod)'..."
	$(call ENSURE_STRUCTURE,$(mod))

	@if [ ! -f $(mod)/src/$(mod).py ]; then \
		echo "ERROR: No existe $(mod)/src/$(mod).py"; \
		exit 1; \
	fi

	@echo ">>> Ejecutando '$(mod)' con GUI..."
	$(PYTHON_GUI) $(mod)/src/$(mod).py

	@echo "✔ FreeCAD GUI abierto."


# ======================================
#   HOLES Y FOOTPRINT (sin cambios)
# ======================================
MODEL = bme280/build/bme280.FCStd
OUT   = gen/holes.txt
PY    = gen/obtain_holes.py

holes:
	@mkdir -p gen
	@echo ">>> Generando $(OUT) desde $(MODEL)..."
	@freecadcmd $(PY) $(MODEL) $(OUT)
	@echo ">>> Listo: $(OUT)"

FOOTPRINT = gen/bme280_auto.kicad_mod
HOLESFILE = gen/holes.txt
PYFP      = gen/make_footprint.py

footprint: holes
	@echo ">>> Generando footprint..."
	@python3 $(PYFP) $(HOLESFILE) $(FOOTPRINT)
	@echo ">>> Listo: $(FOOTPRINT)"

# ======================================
#   DESIGN SEQUENCE (pipeline completo)
# ======================================

# Headless, sin GUI
ds: bme280 holes footprint debug
	@echo ">> DS completo (sin GUI) listo, comandante."

# Con GUI para vista previa
dsp: bme280_gui holes footprint debug
	@echo ">> DSP completo con vista previa. Despliegue autorizado."

debug:
	@echo ">>> DEBUG:"
	@echo "    FCStd: $(GEN)/holes.json"
	@echo "    Mod  : $(GEN)/$(MODULE)_auto.kicad_mod"
	@echo ">>> Todo en orden, comandante."
