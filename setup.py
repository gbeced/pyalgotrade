#!/usr/bin/env python

from distutils.core import setup

setup(name='PyAlgoTrade',
	version='0.2',
	description='Python Algorithmic Trading',
	long_description='Python library for backtesting stock trading strategies.',
	author='Gabriel Martin Becedillas Ruiz',
	author_email='gabriel.becedillas@gmail.com',
	url='http://gbeced.github.com/pyalgotrade/',
	download_url='http://gbeced.github.com/pyalgotrade/releases/PyAlgoTrade-0.2.tar.gz',
	packages=['pyalgotrade',
		'pyalgotrade.tools',
		'pyalgotrade.barfeed',
		'pyalgotrade.optimizer',
		'pyalgotrade.technical'],
)
