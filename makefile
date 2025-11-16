# ======================================
#   CONFIGURACIÓN
# ======================================
SHELL := /bin/bash
PYTHON_HEADLESS := freecadcmd
PYTHON_GUI      := freecad

# ======================================
#   DETECCIÓN AUTOMÁTICA DE MÓDULOS
# ======================================
# Detectar módulos estándar (carpetas con src/)
# Normaliza rutas eliminando el slash final
MODULE_DIRS := $(patsubst %/,%,$(dir $(wildcard */src)))

# Detectar scripts sueltos en raíz (para normalizar después)
ROOT_PYS := $(basename $(notdir $(wildcard *.py)))

# Combinar todos los módulos detectados
MODULES := $(sort $(MODULE_DIRS) $(ROOT_PYS))

# Targets GUI generados automáticamente
MODULES_GUI := $(addsuffix _gui,$(MODULES))

# Targets para generar holes.json
MODULES_HOLES := $(addsuffix _holes,$(MODULES))

# Targets para generar footprints
MODULES_FOOTPRINT := $(addsuffix _footprint,$(MODULES))

# Scripts de generación
OBTAIN_HOLES := gen/obtain_holes.py
MAKE_FOOTPRINT := gen/make_footprint.py

.PHONY: $(MODULES) $(MODULES_GUI) $(MODULES_HOLES) $(MODULES_FOOTPRINT) $(MODULES_STEPS) help normalize list-modules holes footprints steps


# ======================================
#   NORMALIZACIÓN DE ESTRUCTURA
# ======================================
# Esta función asegura que cada módulo tenga la estructura estándar:
#   modulo/
#     src/
#       modulo.py
#     build/
define ENSURE_STRUCTURE
	@echo ">>> Normalizando estructura para '$(1)'..."
	@if [ -d "$(1)" ]; then \
		if [ ! -d "$(1)/src" ] || [ ! -d "$(1)/build" ]; then \
			echo ">>> Creando estructura faltante..."; \
			mkdir -p "$(1)/src" "$(1)/build"; \
		else \
			echo ">>> Estructura correcta."; \
		fi; \
	else \
		echo ">>> Creando directorio y estructura estándar..."; \
		mkdir -p "$(1)/src" "$(1)/build"; \
	fi
	@if [ -f "$(1).py" ]; then \
		echo ">>> Detectado archivo suelto: $(1).py → moviendo a $(1)/src/$(1).py"; \
		mkdir -p "$(1)/src"; \
		mv "$(1).py" "$(1)/src/$(1).py"; \
	fi
endef


# ======================================
#   HELP
# ======================================
help:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Makefile para normalización y ejecución de módulos FreeCAD"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "Uso:"
	@echo "  make <modulo>           - Ejecuta módulo en modo headless (freecadcmd)"
	@echo "  make <modulo>_gui       - Ejecuta módulo con GUI (freecad)"
	@echo "  make <modulo>_holes     - Genera gen/<modulo>_holes.json desde FCStd"
	@echo "  make <modulo>_footprint - Genera gen/<modulo>_auto.kicad_mod desde holes.json"
	@echo "  make <modulo>_steps      - Exporta <modulo>/build/<modulo>.step desde FCStd"
	@echo "  make holes               - Genera holes.json para todos los módulos"
	@echo "  make footprints          - Genera footprints para todos los módulos"
	@echo "  make steps               - Exporta STEPs para todos los módulos"
	@echo "  make normalize           - Normaliza estructura de todos los módulos"
	@echo "  make list-modules       - Lista todos los módulos detectados"
	@echo ""
	@echo "Módulos detectados:"
	@if [ -z "$(MODULES)" ]; then \
		echo "  (ninguno)"; \
	else \
		for m in $(MODULES); do echo "  • $$m"; done; \
	fi
	@echo ""


# ======================================
#   LISTAR MÓDULOS
# ======================================
list-modules:
	@echo "Módulos detectados:"
	@if [ -z "$(MODULES)" ]; then \
		echo "  (ninguno)"; \
	else \
		for m in $(MODULES); do \
			if [ -f "$$m/src/$$m.py" ]; then \
				echo "  ✓ $$m"; \
			else \
				echo "  ✗ $$m (falta $$m/src/$$m.py)"; \
			fi; \
		done; \
	fi


# ======================================
#   NORMALIZAR TODOS LOS MÓDULOS
# ======================================
normalize:
	@echo ">>> Normalizando estructura de todos los módulos..."
	@for mod in $(MODULES); do \
		echo ">>> Normalizando estructura para '$$mod'..."; \
		if [ -d "$$mod" ]; then \
			if [ ! -d "$$mod/src" ] || [ ! -d "$$mod/build" ]; then \
				echo ">>> Creando estructura faltante..."; \
				mkdir -p "$$mod/src" "$$mod/build"; \
			else \
				echo ">>> Estructura correcta."; \
			fi; \
		else \
			echo ">>> Creando directorio y estructura estándar..."; \
			mkdir -p "$$mod/src" "$$mod/build"; \
		fi; \
		if [ -f "$$mod.py" ]; then \
			echo ">>> Detectado archivo suelto: $$mod.py → moviendo a $$mod/src/$$mod.py"; \
			mkdir -p "$$mod/src"; \
			mv "$$mod.py" "$$mod/src/$$mod.py"; \
		fi; \
	done
	@echo "✔ Normalización completa."


# ======================================
#   HEADLESS (freecadcmd)
# ======================================
$(MODULES):
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Módulo: $@"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	$(call ENSURE_STRUCTURE,$@)
	@if [ ! -f "$@/src/$@.py" ]; then \
		echo "❌ ERROR: No existe $@/src/$@.py"; \
		echo "   Ejecuta 'make normalize' para normalizar la estructura."; \
		exit 1; \
	fi
	@echo ">>> Ejecutando '$@' (modo headless)..."
	@$(PYTHON_HEADLESS) "$@/src/$@.py"
	@echo "✔ Completado."


# ======================================
#   GUI (freecad)
# ======================================
$(MODULES_GUI):
	$(eval mod := $(subst _gui,,$@))
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Módulo GUI: $(mod)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	$(call ENSURE_STRUCTURE,$(mod))
	@if [ ! -f "$(mod)/src/$(mod).py" ]; then \
		echo "❌ ERROR: No existe $(mod)/src/$(mod).py"; \
		echo "   Ejecuta 'make normalize' para normalizar la estructura."; \
		exit 1; \
	fi
	@echo ">>> Abriendo FreeCAD GUI..."
	@$(PYTHON_GUI) "$(mod)/src/$(mod).py"
	@echo "✔ GUI abierta."


# ======================================
#   GENERACIÓN DE HOLES.JSON
# ======================================
# Genera gen/<modulo>_holes.json desde el archivo FCStd del módulo
$(MODULES_HOLES):
	@mod=$$(echo "$@" | sed 's/_holes$$//'); \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo "  Generando holes.json para: $$mod"; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	FCSTD="$$mod/build/$$mod.FCStd"; \
	OUT="gen/$${mod}_holes.json"; \
	if [ ! -f "$$FCSTD" ]; then \
		echo "❌ ERROR: No existe $$FCSTD"; \
		echo "   Ejecuta 'make $$mod' primero para generar el archivo FCStd."; \
		exit 1; \
	fi; \
	echo ">>> Procesando $$FCSTD..."; \
	mkdir -p gen; \
	FCSTD_FILE="$$FCSTD" OUT_FILE="$$OUT" $(PYTHON_HEADLESS) -c "exec(open('$(OBTAIN_HOLES)').read())"; \
	echo "✔ Generado: $$OUT"


# ======================================
#   GENERAR HOLES PARA TODOS LOS MÓDULOS
# ======================================
holes: $(MODULES_HOLES)
	@echo "✔ Todos los archivos holes.json generados."


# ======================================
#   GENERACIÓN DE FOOTPRINTS
# ======================================
# Genera gen/<modulo>_auto.kicad_mod desde gen/<modulo>_holes.json
$(MODULES_FOOTPRINT):
	@mod=$$(echo "$@" | sed 's/_footprint$$//'); \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo "  Generando footprint para: $$mod"; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	HOLES_JSON="gen/$${mod}_holes.json"; \
	OUT_FOOT="gen/$${mod}_auto.kicad_mod"; \
	if [ ! -f "$$HOLES_JSON" ]; then \
		echo "❌ ERROR: No existe $$HOLES_JSON"; \
		echo "   Ejecuta 'make $${mod}_holes' primero para generar el archivo holes.json."; \
		exit 1; \
	fi; \
	echo ">>> Procesando $$HOLES_JSON..."; \
	if python3 $(MAKE_FOOTPRINT) "$$HOLES_JSON" "$$OUT_FOOT" && [ -f "$$OUT_FOOT" ]; then \
		echo "✔ Generado: $$OUT_FOOT"; \
	else \
		echo "⚠ No se generó footprint (sin pines o error)"; \
	fi


# ======================================
#   GENERAR FOOTPRINTS PARA TODOS LOS MÓDULOS
# ======================================
footprints: $(MODULES_FOOTPRINT)
	@echo "✔ Todos los footprints generados."


# ======================================
#   EXPORTACIÓN DE ARCHIVOS STEP
# ======================================
MODULES_STEPS := $(addsuffix _steps,$(MODULES))

$(MODULES_STEPS):
	@mod=$$(echo "$@" | sed 's/_steps$$//'); \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo "  Exportando STEP para: $$mod"; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	FCSTD="$$mod/build/$$mod.FCStd"; \
	OUT_STEP="$$mod/build/$$mod.step"; \
	if [ ! -f "$$FCSTD" ]; then \
		echo "❌ ERROR: No existe $$FCSTD"; \
		echo "   Ejecuta 'make $$mod' primero para generar el archivo FCStd."; \
		exit 1; \
	fi; \
	echo ">>> Exportando $$FCSTD → $$OUT_STEP"; \
	FCSTD_FILE="$$FCSTD" OUT_STEP_FILE="$$OUT_STEP" $(PYTHON_HEADLESS) -c "exec(open('gen/export_step.py').read())"; \
	if [ -f "$$OUT_STEP" ]; then \
		echo "✔ STEP generado: $$OUT_STEP"; \
	else \
		echo "❌ ERROR: No se generó el archivo STEP"; \
		exit 1; \
	fi


# ======================================
#   EXPORTAR STEPS PARA TODOS LOS MÓDULOS
# ======================================
steps: $(MODULES_STEPS)
	@echo "✔ Todos los archivos STEP generados."
