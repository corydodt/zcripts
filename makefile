SHELL			:= /bin/bash
EXE				:= zcripts
SOURCES			:= src/zcripts/*.py # src/zcripts/*/*.py


$(EXE): $(SOURCES)
	python3 -m nuitka src/zcripts/zcripts_cli.py \
		--onefile \
		--output-filename=zcripts \
		--warn-unusual-code \
		--include-package=zcripts


build-deps:
	@echo you may also need to install epel-release for these packages
	@echo e.g.: sudo dnf install -y epel-release
	pip install patchelf
	sudo dnf -y install python-devel gcc
