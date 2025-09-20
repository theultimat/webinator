BUILD_DIR := build
SITE_DIR  := $(BUILD_DIR)/site
VENV_DIR  := $(BUILD_DIR)/venv

PYTHON := python
PIP    := pip


# Assumes webinator has been checked out in subdirectory "webinator" of the main
# repository but if this isn't the case override the variable below.
WEBINATOR_DIR ?= webinator


# Default rule builds the complete site.
all: webinate

clean:
	rm -rf $(BUILD_DIR)

.PHONY: all clean


# Create python virtual environment for reproducible builds.
VENV_ACTIVATE := $(VENV_DIR)/bin/activate
VENV_REQ      ?= $(WEBINATOR_DIR)/requirements.txt
VENV_READY    := $(VENV_DIR)/.ready

venv: $(VENV_READY)

$(VENV_DIR):
	@mkdir -p $(@D)
	$(PYTHON) -m venv $@

$(VENV_READY): $(VENV_REQ) $(VENV_DIR)
	. $(VENV_ACTIVATE) && $(PIP) install -r $<
	touch $@

.PHONY: venv


# Copy over static content if any exists.
STATIC_DIR  ?=
STATIC_SRCS := $(if $(STATIC_DIR),$(shell find $(STATIC_DIR) -type f -name '*'))
STATIC_OUTS := $(patsubst $(STATIC_DIR)/%,$(SITE_DIR)/%,$(STATIC_SRCS))

static: $(STATIC_OUTS)

$(SITE_DIR)/%: $(STATIC_DIR)/%
	@mkdir -p $(@D)
	cp $< $@

.PHONY: static


# Convert markdown inputs to HTML. This assumes a number of inputs have been set
# externally and will complain if they haven't.
ifeq ($(HTML_SRC_DIR),)
$(error No HTML_SRC_DIR specified!)
endif

ifeq ($(HTML_TEMPLATE),)
$(error No HTML_TEMPLATE specified!)
endif

HTML_DEPS ?=
HTML_SRCS := $(shell find $(HTML_SRC_DIR) -type f -name '*.md')
HTML_OUTS := $(patsubst $(HTML_SRC_DIR)/%.md,$(SITE_DIR)/%,$(HTML_SRCS))
WEBINATE  := $(WEBINATOR_DIR)/webinate.py

webinate: $(HTML_OUTS) static

$(SITE_DIR)/%: $(HTML_SRC_DIR)/%.md $(HTML_TEMPLATE) $(HTML_DEPS) $(VENV_READY)
	@mkdir -p $(@D)
	. $(VENV_ACTIVATE) && $(PYTHON) $(WEBINATE) -o $@ -t $(HTML_TEMPLATE) $<

.PHONY: webinate
