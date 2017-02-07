#!/usr/bin/env python

# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='PyAlgoTrade',
    version='0.18',
    description='Python Algorithmic Trading',
    long_description='Python library for backtesting stock trading strategies.',
    author='Gabriel Martin Becedillas Ruiz',
    author_email='pyalgotrade@gmail.com',
    url='http://gbeced.github.io/pyalgotrade/',
    download_url='http://sourceforge.net/projects/pyalgotrade/files/0.18/PyAlgoTrade-0.18.tar.gz/download',
    packages=[
        'pyalgotrade',
        'pyalgotrade.barfeed',
        'pyalgotrade.bitcoincharts',
        'pyalgotrade.bitstamp',
        'pyalgotrade.broker',
        'pyalgotrade.dataseries',
        'pyalgotrade.feed',
        'pyalgotrade.optimizer',
        'pyalgotrade.stratanalyzer',
        'pyalgotrade.strategy',
        'pyalgotrade.talibext',
        'pyalgotrade.technical',
        'pyalgotrade.tools',
        'pyalgotrade.twitter',
        'pyalgotrade.utils',
        'pyalgotrade.websocket',
    ],
    install_requires=[
        "numpy",
        "pytz",
        "python-dateutil",
        "requests",
    ],
    extras_require={
        'Scipy':  ["scipy"],
        'TALib':  ["Cython", "TA-Lib"],
        'Plotting':  ["matplotlib"],
        'Bitstamp':  ["ws4py>=0.3.4", "tornado"],
        'Twitter':  ["tweepy"],
    },
)
