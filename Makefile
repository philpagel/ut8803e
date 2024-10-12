VERSION="0.0.1"

help:
	@echo "The following make targets are available:\n"
	@echo "   dep          install dependencies (requirements)"
	@echo "   dep-dev      install dependencies for packaging"
	@echo "   build        build python package"
	@echo "   install      install python package"
	@echo "   pypi         upload package to pypi"
	@echo "   clean        clean up package and cruft"
.PHONEY: help


dep:
	python -m pip install -r requirements.txt
.PHONEY: dep

dep-dev:
	python -m pip install -r requirements-dev.txt --upgrade
.PHONEY: dep-dev

build: 
	python -m build
.PHONEY: build

install: 
	python -m pip install dist/ut8803e-$(VERSION).tar.gz
.PHONEY: install

clean:
	rm -rf dist
	rm -rf src/ut8803e.egg-info
	rm -rf src/ut8803e/__pycache__
.PHONEY: clean
