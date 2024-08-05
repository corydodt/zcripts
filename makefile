SHELL			:= /bin/bash
EXE				:= zcripts
SOURCES			:= src/zcripts/*.py # src/zcripts/*/*.py

-include .env

ifndef BUILD_ARCH
$(error BUILD_ARCH is undefined)
endif

SELF_INSTALLER  := ./install-zcripts_$(BUILD_ARCH).run


exe: $(EXE)
$(EXE) $(EXE)_linux_$(BUILD_ARCH): $(SOURCES)
	python3 -m nuitka src/zcripts/zcripts_cli.py \
		--onefile \
		--output-filename=zcripts \
		--warn-unusual-code \
		--include-package=zcripts \
		--static-libpython=auto
	cp -v ./zcripts ./zcripts_linux_$(BUILD_ARCH)
	@ls -l "$(EXE)" "$(EXE)_linux_$(BUILD_ARCH)"

installer: $(SELF_INSTALLER)
$(SELF_INSTALLER): tmp := $(shell mktemp -u -d --suffix .zcripts-installer)
$(SELF_INSTALLER): $(EXE)
	mkdir -p $(tmp)
	cp -v bin/self-installer-init "$(tmp)/"
	cp -v ./zcripts_linux_$(BUILD_ARCH) "$(tmp)/zcripts"
	makeself "$(tmp)" $@ "zcripts binary installer" ./self-installer-init
	@rm -rf $(tmp)
	@ls -l "$@"

build-deps:
	@echo you may also need to install epel-release for these packages
	@echo e.g.: sudo dnf install -y epel-release
	pip install patchelf
	sudo dnf -y install python-devel gcc ccache makeself


format:
	python -m black src/zcripts
