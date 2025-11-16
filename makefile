SHELL = /usr/bin/fish

PYTHON_HEADLESS = freecadcmd
PYTHON_GUI      = freecad

# Detectar módulos estándar (carpetas con src/)
MODULE_DIRS := $(patsubst %/,%,$(dir $(wildcard */src)))

# Detectar scripts sueltos en raíz
ROOT_PYS    := $(basename $(notdir $(wildcard *.py)))

MODULES     := $(MODULE_DIRS) $(ROOT_PYS)
MODULES_GUI := $(addsuffix _gui,$(MODULES))

.PHONY: $(MODULES) $(MODULES_GUI) help


# ======================================
#   ENSURE_STRUCTURE (fish-only)
#   Una sola línea interna, sin comillas dobles internas
# ======================================
define ENSURE_STRUCTURE
if test -d $(1); if test -d $(1)/src -a -d $(1)/build; echo '>>> $(1): estructura correcta.'; else; echo '>>> $(1): existe pero falta estructura, creando...'; mkdir -p $(1)/src $(1)/build; end; else; echo '>>> $(1): creando estructura estándar...'; mkdir -p $(1)/src $(1)/build; end; if test -f $(1).py; echo '>>> Detectado archivo suelto: $(1).py → moviendo a $(1)/src/$(1).py'; mkdir -p $(1)/src; mv $(1).py $(1)/src/$(1).py; end
endef


help:
	@echo "Uso:"
	@echo "  make <modulo>        - Ejecuta headless (FreeCADCMD)"
	@echo "  make <modulo>_gui    - Ejecuta GUI (FreeCAD)"
	@echo
	@echo "Módulos detectados:"
	@for m in $(MODULES); echo "  - $$m"; end


# ======================================
#   HEADLESS
# ======================================
$(MODULES):
	@echo ">>> Módulo '$@'"
	@fish -c "$(call ENSURE_STRUCTURE,$@)"

	@fish -c "if test ! -f $@/src/$@.py; echo 'ERROR: Falta $@/src/$@.py'; exit 1; end"

	@echo ">>> Ejecutando '$@' (headless)..."
	@$(PYTHON_HEADLESS) "$@/src/$@.py"
	@echo "✔ Listo."


# ======================================
#   GUI
# ======================================
$(MODULES_GUI):
	$(eval mod := $(subst _gui,,$@))

	@echo ">>> Módulo GUI '$(mod)'"
	@fish -c "$(call ENSURE_STRUCTURE,$(mod))"

	@fish -c "if test ! -f $(mod)/src/$(mod).py; echo 'ERROR: Falta $(mod)/src/$(mod).py'; exit 1; end"

	@echo ">>> Abriendo FreeCAD GUI..."
	@$(PYTHON_GUI) "$(mod)/src/$(mod).py"
	@echo "✔ GUI abierta."
