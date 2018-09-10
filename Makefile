.PHONY: doc clean build flake8 test testpy27

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

all: test

doc:
	cd doc; make html

clean:
	find . -name *.pyc -delete
	find . -name .coverage -delete
	find . -name .noseids -delete
	find . -name htmlcov -exec rm -rf {} \;
	# Clean packages
	rm -rf dist/PyAlgoTrade-*.tar.gz
	# Clean tox
	rm -rf .tox
	# Clean doc
	cd doc; make clean

build:
	rm -rf dist/PyAlgoTrade-*.tar.gz
	python setup.py sdist

flake8:
	flake8 testcases --max-line-length=120
	flake8 pyalgotrade --max-line-length=120

testpy27: flake8
	tox -v -e py27

test: flake8
	tox -v
