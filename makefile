PYTHON = freecad

# Detectar carpetas que tienen src/, normalizando sin slash final
MODULE_DIRS := $(patsubst %/,%,$(dir $(wildcard */src)))

# Detectar módulos con .py suelto en raíz
ROOT_PYS := $(basename $(notdir $(wildcard *.py)))

# Unir módulos detectados
MODULES := $(MODULE_DIRS) $(ROOT_PYS)

.PHONY: $(MODULES) help

help:
	@echo "Uso: make <modulo>"
	@echo "Modulos disponibles:"
	@for m in $(MODULES); do echo "  - $$m"; done


# --- Crear estructura estándar ---
define ENSURE_STRUCTURE
	@mkdir -p $(1)/src
	@mkdir -p $(1)/build
	@if [ -f $(1).py ]; then \
		echo ">>> Detectado archivo suelto: $(1).py"; \
		echo ">>> Moviendo a $(1)/src/$(1).py"; \
		mv $(1).py $(1)/src/$(1).py; \
	fi
endef


# --- Ejecutar módulo ---
define RUN_MODULE
	@echo ">>> Ejecutando módulo '$(1)'..."
	$(PYTHON) $(1)/src/$(1).py
endef


# --- Regla dinámica ---
$(MODULES):
	@echo ">>> Verificando módulo '$@'..."
	$(call ENSURE_STRUCTURE,$@)
	@if [ ! -f $@/src/$@.py ]; then \
		echo "ERROR: No existe $@/src/$@.py"; \
		echo "Crea $@.py en el root para bootstrap automático."; \
		exit 1; \
	fi
	$(call RUN_MODULE,$@)
