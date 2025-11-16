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

.PHONY: $(MODULES) $(MODULES_GUI) help normalize list-modules


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
	@echo "  make normalize          - Normaliza estructura de todos los módulos"
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
