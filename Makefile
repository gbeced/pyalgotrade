.PHONY: doc clean build flake8 test testpy27 \
	docker-build docker-push docker-test

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

docker-build:
	# Build and tag Python 2.7 images
	docker pull python:2.7
	docker build -f docker/Dockerfile --build-arg PYTHON_VERSION=2.7 -t pyalgotrade:0.20 docker
	docker tag pyalgotrade:0.20 pyalgotrade:0.20-py27
	docker tag pyalgotrade:0.20 gbecedillas/pyalgotrade:0.20
	docker tag pyalgotrade:0.20-py27 gbecedillas/pyalgotrade:0.20-py27

	# Build and tag Python 3.7 images
	docker pull python:3.7
	docker build -f docker/Dockerfile --build-arg PYTHON_VERSION=3.7 -t pyalgotrade:0.20-py37 docker
	docker tag pyalgotrade:0.20-py37 gbecedillas/pyalgotrade:0.20-py37

docker-push: docker-build
	# Push images
	docker login --username=gbecedillas
	# docker push gbecedillas/pyalgotrade:0.20
	docker push gbecedillas/pyalgotrade:0.20-py27
	docker push gbecedillas/pyalgotrade:0.20-py37

docker-test: docker-build
	docker build -t pyalgotrade_testcases -f travis/Dockerfile .
	docker run pyalgotrade_testcases /bin/bash -c "cd /tmp/pyalgotrade; ./run_tests.sh"
