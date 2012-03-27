#!/usr/bin/env python

from distutils.core import setup

setup(name='PyAlgoTrade',
	version='0.1',
	description='Python Algorithmic Trading',
	author='Gabriel Martin Becedillas Ruiz',
	author_email='gabriel.becedillas@gmail.com',
	url='http://gbeced.github.com/pyalgotrade/',
	packages=['pyalgotrade',
		'pyalgotrade.barfeed',
		'pyalgotrade.optimizer',
		'pyalgotrade.technical'],
)
