.PHONY: clean build test

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8


clean:
	find . -name *.pyc -delete
	find . -name .coverage -delete
	find . -name .noseids -delete
	find . -name htmlcov -exec rm -rf {} \;
	rm -rf dist/PyAlgoTrade-*.tar.gz
	rm -rf .tox

build: test
	rm -rf dist/PyAlgoTrade-*.tar.gz
	python setup.py sdist

test:
	flake8 testcases --max-line-length=120
	flake8 pyalgotrade --max-line-length=120
	tox
