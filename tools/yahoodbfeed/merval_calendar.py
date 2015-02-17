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

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

skip_dates = {}


def skip_date(year, month, day):
    skip_dates.setdefault(year, {})
    skip_dates[year].setdefault(month, [])
    skip_dates[year][month].append(day)

# Feriados inamovibles
for year in range(2000, 2014):
    skip_date(year, 1, 1)  # Anio nuevo
    skip_date(year, 5, 1)  # Dia del Trabajador
    skip_date(year, 5, 25)  # Revolucion de Mayo
    skip_date(year, 7, 9)  # Independencia
    skip_date(year, 12, 8)  # Inmaculada Concepcion de Maria
    skip_date(year, 12, 25)  # Navidad

    if year >= 2006:
        skip_date(year, 3, 24)  # Dia Nacional de la Memoria por la Verdad y la Justicia

    if year >= 2007:
        skip_date(year, 4, 2)  # Dia del Veterano y de los Caidos en la Guerra de Malvinas

# 2010
# Feriados inamovibles
skip_date(2010, 4, 2)  # Viernes Santo
skip_date(2010, 5, 24)  # Feriado nacional
skip_date(2010, 10, 27)  # Censo
# Feriados trasladables
skip_date(2010, 6, 21)  # Paso a la Inmortalidad del General Manuel Belgrano
skip_date(2010, 8, 16)  # Paso a la Inmortalidad del General Jose de San Martin
skip_date(2010, 10, 11)  # Dia del Respeto a la Diversidad Cultural
skip_date(2010, 11, 22)  # Dia de la Soberania Nacional
skip_date(2010, 4, 24)  # Dia de accion por la tolerancia y el respeto entre los pueblos

# 2011
# Feriados inamovibles
skip_date(2011, 3, 7)  # Carnaval
skip_date(2011, 3, 8)  # Carnaval
skip_date(2011, 3, 25)  # Feriado Puente Turistico
skip_date(2011, 4, 22)  # Viernes Santo
skip_date(2011, 6, 20)  # Paso a la Inmortalidad del General Manuel Belgrano
skip_date(2011, 12, 9)  # Feriado Puente Turistico
skip_date(2011, 12, 25)  # Navidad
# Feriados trasladables
skip_date(2011, 8, 22)  # Paso a la Inmortalidad del General Jose de San Martin
skip_date(2011, 10, 10)  # Dia del Respeto a la Diversidad Cultural
skip_date(2011, 11, 28)  # Dia de la Soberania Nacional
# Dias no laborables
skip_date(2011, 4, 21)  # Jueves Santo Festividad Cristiana
skip_date(2011, 4, 24)  # Dia de accion por la tolerancia y el respeto entre los pueblos

# 2012
# Feriados inamovibles
skip_date(2012, 2, 20)  # Carnaval
skip_date(2012, 2, 21)  # Carnaval
skip_date(2012, 2, 27)  # Dia del Bicentenario de la Creacion y Primera Jura de la Bandera Argentina
skip_date(2012, 4, 6)  # Viernes Santo
skip_date(2012, 4, 30)  # Feriado Puente Turistico
skip_date(2012, 6, 20)  # Paso a la Inmortalidad del General Manuel Belgrano
skip_date(2012, 9, 24)  # Bicentenario de la Batalla de Tucuman
skip_date(2012, 12, 24)  # Feriado Puente Turistico
skip_date(2012, 12, 25)  # Navidad
# Feriados trasladables
skip_date(2012, 8, 20)  # Paso a la Inmortalidad del General Jose de San Martin
skip_date(2012, 10, 8)  # Dia del Respeto a la Diversidad Cultural
skip_date(2012, 11, 26)  # Dia de la Soberania Nacional
# Dias no laborables
skip_date(2012, 4, 5)  # Jueves Santo Festividad Cristiana
skip_date(2012, 4, 24)  # Dia de accion por la tolerancia y el respeto entre los pueblos

# 2013
# Feriados inamovibles
skip_date(2013, 1, 31)  # Bicentenario de la Asamblea General Constituyente de 1813
skip_date(2013, 2, 11)  # Carnaval
skip_date(2013, 2, 12)  # Carnaval
skip_date(2013, 2, 20)  # Dia de la Batalla de Salta
skip_date(2013, 3, 29)  # Viernes Santo
skip_date(2013, 4, 1)  # Feriado Puente Turistico
skip_date(2010, 6, 20)  # Paso a la Inmortalidad del General Manuel Belgrano
skip_date(2013, 6, 21)  # Feriado Puente Turistico
# Feriados trasladables
skip_date(2013, 8, 19)  # Paso a la Inmortalidad del General Jose de San Martin
skip_date(2013, 10, 14)  # Dia del Respeto a la Diversidad Cultural
skip_date(2013, 11, 25)  # Dia de la Soberania Nacional
# Dias no laborables
skip_date(2013, 3, 28)  # Jueves Santo
skip_date(2013, 4, 24)  # Dia de accion por la tolerancia y el respeto entre los pueblos


def is_trading_day(dateTime):
    return dateTime.day not in skip_dates.get(dateTime.year, {}).get(dateTime.month, [])
