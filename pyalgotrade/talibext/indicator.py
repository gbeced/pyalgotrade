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

import talib
import numpy


# Returns the last values of a dataseries as a numpy.array, or None if not enough values could be retrieved from the dataseries.
def value_ds_to_numpy(ds, count):
    ret = None
    try:
        values = ds[count*-1:]
        ret = numpy.array([float(value) for value in values])
    except IndexError:
        pass
    except TypeError:  # In case we try to convert None to float.
        pass
    return ret


# Returns the last open values of a bar dataseries as a numpy.array, or None if not enough values could be retrieved from the dataseries.
def bar_ds_open_to_numpy(barDs, count):
    return value_ds_to_numpy(barDs.getOpenDataSeries(), count)


# Returns the last high values of a bar dataseries as a numpy.array, or None if not enough values could be retrieved from the dataseries.
def bar_ds_high_to_numpy(barDs, count):
    return value_ds_to_numpy(barDs.getHighDataSeries(), count)


# Returns the last low values of a bar dataseries as a numpy.array, or None if not enough values could be retrieved from the dataseries.
def bar_ds_low_to_numpy(barDs, count):
    return value_ds_to_numpy(barDs.getLowDataSeries(), count)


# Returns the last close values of a bar dataseries as a numpy.array, or None if not enough values could be retrieved from the dataseries.
def bar_ds_close_to_numpy(barDs, count):
    return value_ds_to_numpy(barDs.getCloseDataSeries(), count)


# Returns the last volume values of a bar dataseries as a numpy.array, or None if not enough values could be retrieved from the dataseries.
def bar_ds_volume_to_numpy(barDs, count):
    return value_ds_to_numpy(barDs.getVolumeDataSeries(), count)


# Calls a talib function with the last values of a dataseries.
def call_talib_with_ds(ds, count, talibFunc, *args, **kwargs):
    data = value_ds_to_numpy(ds, count)
    if data is None:
        return None
    return talibFunc(data, *args, **kwargs)


# hlcv: High, Low, Close and Volume.
def call_talib_with_hlcv(barDs, count, talibFunc, *args, **kwargs):
    high = bar_ds_high_to_numpy(barDs, count)
    if high is None:
        return None

    low = bar_ds_low_to_numpy(barDs, count)
    if low is None:
        return None

    close = bar_ds_close_to_numpy(barDs, count)
    if close is None:
        return None

    volume = bar_ds_volume_to_numpy(barDs, count)
    if volume is None:
        return None

    return talibFunc(high, low, close, volume, *args, **kwargs)


def call_talib_with_hlc(barDs, count, talibFunc, *args, **kwargs):
    high = bar_ds_high_to_numpy(barDs, count)
    if high is None:
        return None

    low = bar_ds_low_to_numpy(barDs, count)
    if low is None:
        return None

    close = bar_ds_close_to_numpy(barDs, count)
    if close is None:
        return None

    return talibFunc(high, low, close, *args, **kwargs)


def call_talib_with_ohlc(barDs, count, talibFunc, *args, **kwargs):
    open_ = bar_ds_open_to_numpy(barDs, count)
    if open_ is None:
        return None

    high = bar_ds_high_to_numpy(barDs, count)
    if high is None:
        return None

    low = bar_ds_low_to_numpy(barDs, count)
    if low is None:
        return None

    close = bar_ds_close_to_numpy(barDs, count)
    if close is None:
        return None

    return talibFunc(open_, high, low, close, *args, **kwargs)


def call_talib_with_hl(barDs, count, talibFunc, *args, **kwargs):
    high = bar_ds_high_to_numpy(barDs, count)
    if high is None:
        return None

    low = bar_ds_low_to_numpy(barDs, count)
    if low is None:
        return None

    return talibFunc(high, low, *args, **kwargs)


######################################################################
## talib wrappers

def AD(barDs, count):
    """Chaikin A/D Line"""
    return call_talib_with_hlcv(barDs, count, talib.AD)


def ADOSC(barDs, count, fastperiod=-2**31, slowperiod=-2**31):
    """Chaikin A/D Oscillator"""
    return call_talib_with_hlcv(barDs, count, talib.ADOSC, fastperiod, slowperiod)


def ADX(barDs, count, timeperiod=-2**31):
    """Average Directional Movement Index"""
    return call_talib_with_hlc(barDs, count, talib.ADX, timeperiod)


def ADXR(barDs, count, timeperiod=-2**31):
    """Average Directional Movement Index Rating"""
    return call_talib_with_hlc(barDs, count, talib.ADXR, timeperiod)


def APO(ds, count, fastperiod=-2**31, slowperiod=-2**31, matype=0):
    """Absolute Price Oscillator"""
    return call_talib_with_ds(ds, count, talib.APO, fastperiod, slowperiod, matype)


def AROON(barDs, count, timeperiod=-2**31):
    """Aroon"""
    ret = call_talib_with_hl(barDs, count, talib.AROON, timeperiod)
    if ret is None:
        ret = (None, None)
    return ret


def AROONOSC(barDs, count, timeperiod=-2**31):
    """Aroon Oscillator"""
    return call_talib_with_hl(barDs, count, talib.AROONOSC, timeperiod)


def ATR(barDs, count, timeperiod=-2**31):
    """Average True Range"""
    return call_talib_with_hlc(barDs, count, talib.ATR, timeperiod)


def AVGPRICE(barDs, count):
    """Average Price"""
    return call_talib_with_ohlc(barDs, count, talib.AVGPRICE)


def BBANDS(ds, count, timeperiod=-2**31, nbdevup=-4e37, nbdevdn=-4e37, matype=0):
    """Bollinger Bands"""
    ret = call_talib_with_ds(ds, count, talib.BBANDS, timeperiod, nbdevup, nbdevdn, matype)
    if ret is None:
        ret = (None, None, None)
    return ret


def BETA(ds1, ds2, count, timeperiod=-2**31):
    """Beta"""
    data1 = value_ds_to_numpy(ds1, count)
    if data1 is None:
        return None
    data2 = value_ds_to_numpy(ds2, count)
    if data2 is None:
        return None
    return talib.BETA(data1, data2, timeperiod)


def BOP(barDs, count):
    """Balance Of Power"""
    return call_talib_with_ohlc(barDs, count, talib.BOP)


def CCI(barDs, count, timeperiod=-2**31):
    """Commodity Channel Index"""
    return call_talib_with_hlc(barDs, count, talib.CCI, timeperiod)


def CDL2CROWS(barDs, count):
    """Two Crows"""
    return call_talib_with_ohlc(barDs, count, talib.CDL2CROWS)


def CDL3BLACKCROWS(barDs, count):
    """Three Black Crows"""
    return call_talib_with_ohlc(barDs, count, talib.CDL3BLACKCROWS)


def CDL3INSIDE(barDs, count):
    """Three Inside Up/Down"""
    return call_talib_with_ohlc(barDs, count, talib.CDL3INSIDE)


def CDL3LINESTRIKE(barDs, count):
    """Three-Line Strike"""
    return call_talib_with_ohlc(barDs, count, talib.CDL3LINESTRIKE)


def CDL3OUTSIDE(barDs, count):
    """Three Outside Up/Down"""
    return call_talib_with_ohlc(barDs, count, talib.CDL3OUTSIDE)


def CDL3STARSINSOUTH(barDs, count):
    """Three Stars In The South"""
    return call_talib_with_ohlc(barDs, count, talib.CDL3STARSINSOUTH)


def CDL3WHITESOLDIERS(barDs, count):
    """Three Advancing White Soldiers"""
    return call_talib_with_ohlc(barDs, count, talib.CDL3WHITESOLDIERS)


def CDLABANDONEDBABY(barDs, count, penetration=-4e37):
    """Abandoned Baby"""
    return call_talib_with_ohlc(barDs, count, talib.CDLABANDONEDBABY, penetration)


def CDLADVANCEBLOCK(barDs, count):
    """Advance Block"""
    return call_talib_with_ohlc(barDs, count, talib.CDLADVANCEBLOCK)


def CDLBELTHOLD(barDs, count):
    """Belt-hold"""
    return call_talib_with_ohlc(barDs, count, talib.CDLBELTHOLD)


def CDLBREAKAWAY(barDs, count):
    """Breakaway"""
    return call_talib_with_ohlc(barDs, count, talib.CDLBREAKAWAY)


def CDLCLOSINGMARUBOZU(barDs, count):
    """Closing Marubozu"""
    return call_talib_with_ohlc(barDs, count, talib.CDLCLOSINGMARUBOZU)


def CDLCONCEALBABYSWALL(barDs, count):
    """Concealing Baby Swallow"""
    return call_talib_with_ohlc(barDs, count, talib.CDLCONCEALBABYSWALL)


def CDLCOUNTERATTACK(barDs, count):
    """Counterattack"""
    return call_talib_with_ohlc(barDs, count, talib.CDLCOUNTERATTACK)


def CDLDARKCLOUDCOVER(barDs, count, penetration=-4e37):
    """Dark Cloud Cover"""
    return call_talib_with_ohlc(barDs, count, talib.CDLDARKCLOUDCOVER, penetration)


def CDLDOJI(barDs, count):
    """Doji"""
    return call_talib_with_ohlc(barDs, count, talib.CDLDOJI)


def CDLDOJISTAR(barDs, count):
    """Doji Star"""
    return call_talib_with_ohlc(barDs, count, talib.CDLDOJISTAR)


def CDLDRAGONFLYDOJI(barDs, count):
    """Dragonfly Doji"""
    return call_talib_with_ohlc(barDs, count, talib.CDLDRAGONFLYDOJI)


def CDLENGULFING(barDs, count):
    """Engulfing Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLENGULFING)


def CDLEVENINGDOJISTAR(barDs, count, penetration=-4e37):
    """Evening Doji Star"""
    return call_talib_with_ohlc(barDs, count, talib.CDLEVENINGDOJISTAR, penetration)


def CDLEVENINGSTAR(barDs, count, penetration=-4e37):
    """Evening Star"""
    return call_talib_with_ohlc(barDs, count, talib.CDLEVENINGSTAR, penetration)


def CDLGAPSIDESIDEWHITE(barDs, count):
    """Up/Down-gap side-by-side white lines"""
    return call_talib_with_ohlc(barDs, count, talib.CDLGAPSIDESIDEWHITE)


def CDLGRAVESTONEDOJI(barDs, count):
    """Gravestone Doji"""
    return call_talib_with_ohlc(barDs, count, talib.CDLGRAVESTONEDOJI)


def CDLHAMMER(barDs, count):
    """Hammer"""
    return call_talib_with_ohlc(barDs, count, talib.CDLHAMMER)


def CDLHANGINGMAN(barDs, count):
    """Hanging Man"""
    return call_talib_with_ohlc(barDs, count, talib.CDLHANGINGMAN)


def CDLHARAMI(barDs, count):
    """Harami Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLHARAMI)


def CDLHARAMICROSS(barDs, count):
    """Harami Cross Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLHARAMICROSS)


def CDLHIGHWAVE(barDs, count):
    """High-Wave Candle"""
    return call_talib_with_ohlc(barDs, count, talib.CDLHIGHWAVE)


def CDLHIKKAKE(barDs, count):
    """Hikkake Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLHIKKAKE)


def CDLHIKKAKEMOD(barDs, count):
    """Modified Hikkake Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLHIKKAKEMOD)


def CDLHOMINGPIGEON(barDs, count):
    """Homing Pigeon"""
    return call_talib_with_ohlc(barDs, count, talib.CDLHOMINGPIGEON)


def CDLIDENTICAL3CROWS(barDs, count):
    """Identical Three Crows"""
    return call_talib_with_ohlc(barDs, count, talib.CDLIDENTICAL3CROWS)


def CDLINNECK(barDs, count):
    """In-Neck Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLINNECK)


def CDLINVERTEDHAMMER(barDs, count):
    """Inverted Hammer"""
    return call_talib_with_ohlc(barDs, count, talib.CDLINVERTEDHAMMER)


def CDLKICKING(barDs, count):
    """Kicking"""
    return call_talib_with_ohlc(barDs, count, talib.CDLKICKING)


def CDLKICKINGBYLENGTH(barDs, count):
    """Kicking - bull/bear determined by the longer marubozu"""
    return call_talib_with_ohlc(barDs, count, talib.CDLKICKINGBYLENGTH)


def CDLLADDERBOTTOM(barDs, count):
    """Ladder Bottom"""
    return call_talib_with_ohlc(barDs, count, talib.CDLLADDERBOTTOM)


def CDLLONGLEGGEDDOJI(barDs, count):
    """Long Legged Doji"""
    return call_talib_with_ohlc(barDs, count, talib.CDLLONGLEGGEDDOJI)


def CDLLONGLINE(barDs, count):
    """Long Line Candle"""
    return call_talib_with_ohlc(barDs, count, talib.CDLLONGLINE)


def CDLMARUBOZU(barDs, count):
    """Marubozu"""
    return call_talib_with_ohlc(barDs, count, talib.CDLMARUBOZU)


def CDLMATCHINGLOW(barDs, count):
    """Matching Low"""
    return call_talib_with_ohlc(barDs, count, talib.CDLMATCHINGLOW)


def CDLMATHOLD(barDs, count, penetration=-4e37):
    """Mat Hold"""
    return call_talib_with_ohlc(barDs, count, talib.CDLMATHOLD, penetration)


def CDLMORNINGDOJISTAR(barDs, count, penetration=-4e37):
    """Morning Doji Star"""
    return call_talib_with_ohlc(barDs, count, talib.CDLMORNINGDOJISTAR, penetration)


def CDLMORNINGSTAR(barDs, count, penetration=-4e37):
    """Morning Star"""
    return call_talib_with_ohlc(barDs, count, talib.CDLMORNINGSTAR, penetration)


def CDLONNECK(barDs, count):
    """On-Neck Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLONNECK)


def CDLPIERCING(barDs, count):
    """Piercing Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLPIERCING)


def CDLRICKSHAWMAN(barDs, count):
    """Rickshaw Man"""
    return call_talib_with_ohlc(barDs, count, talib.CDLRICKSHAWMAN)


def CDLRISEFALL3METHODS(barDs, count):
    """Rising/Falling Three Methods"""
    return call_talib_with_ohlc(barDs, count, talib.CDLRISEFALL3METHODS)


def CDLSEPARATINGLINES(barDs, count):
    """Separating Lines"""
    return call_talib_with_ohlc(barDs, count, talib.CDLSEPARATINGLINES)


def CDLSHOOTINGSTAR(barDs, count):
    """Shooting Star"""
    return call_talib_with_ohlc(barDs, count, talib.CDLSHOOTINGSTAR)


def CDLSHORTLINE(barDs, count):
    """Short Line Candle"""
    return call_talib_with_ohlc(barDs, count, talib.CDLSHORTLINE)


def CDLSPINNINGTOP(barDs, count):
    """Spinning Top"""
    return call_talib_with_ohlc(barDs, count, talib.CDLSPINNINGTOP)


def CDLSTALLEDPATTERN(barDs, count):
    """Stalled Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLSTALLEDPATTERN)


def CDLSTICKSANDWICH(barDs, count):
    """Stick Sandwich"""
    return call_talib_with_ohlc(barDs, count, talib.CDLSTICKSANDWICH)


def CDLTAKURI(barDs, count):
    """Takuri (Dragonfly Doji with very long lower shadow)"""
    return call_talib_with_ohlc(barDs, count, talib.CDLTAKURI)


def CDLTASUKIGAP(barDs, count):
    """Tasuki Gap"""
    return call_talib_with_ohlc(barDs, count, talib.CDLTASUKIGAP)


def CDLTHRUSTING(barDs, count):
    """Thrusting Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLTHRUSTING)


def CDLTRISTAR(barDs, count):
    """Tristar Pattern"""
    return call_talib_with_ohlc(barDs, count, talib.CDLTRISTAR)


def CDLUNIQUE3RIVER(barDs, count):
    """Unique 3 River"""
    return call_talib_with_ohlc(barDs, count, talib.CDLUNIQUE3RIVER)


def CDLUPSIDEGAP2CROWS(barDs, count):
    """Upside Gap Two Crows"""
    return call_talib_with_ohlc(barDs, count, talib.CDLUPSIDEGAP2CROWS)


def CDLXSIDEGAP3METHODS(barDs, count):
    """Upside/Downside Gap Three Methods"""
    return call_talib_with_ohlc(barDs, count, talib.CDLXSIDEGAP3METHODS)


def CMO(ds, count, timeperiod=-2**31):
    """Chande Momentum Oscillator"""
    return call_talib_with_ds(ds, count, talib.CMO, timeperiod)


def CORREL(ds1, ds2, count, timeperiod=-2**31):
    """Pearson's Correlation Coefficient (r)"""
    data1 = value_ds_to_numpy(ds1, count)
    if data1 is None:
        return None
    data2 = value_ds_to_numpy(ds2, count)
    if data2 is None:
        return None
    return talib.CORREL(data1, data2, timeperiod)


def DEMA(ds, count, timeperiod=-2**31):
    """Double Exponential Moving Average"""
    return call_talib_with_ds(ds, count, talib.DEMA, timeperiod)


def DX(barDs, count, timeperiod=-2**31):
    """Directional Movement Index"""
    return call_talib_with_hlc(barDs, count, talib.DX, timeperiod)


def EMA(ds, count, timeperiod=-2**31):
    """Exponential Moving Average"""
    return call_talib_with_ds(ds, count, talib.EMA, timeperiod)


def HT_DCPERIOD(ds, count):
    """Hilbert Transform - Dominant Cycle Period"""
    return call_talib_with_ds(ds, count, talib.HT_DCPERIOD)


def HT_DCPHASE(ds, count):
    """Hilbert Transform - Dominant Cycle Phase"""
    return call_talib_with_ds(ds, count, talib.HT_DCPHASE)


def HT_PHASOR(ds, count):
    """Hilbert Transform - Phasor Components"""
    ret = call_talib_with_ds(ds, count, talib.HT_PHASOR)
    if ret is None:
        ret = (None, None)
    return ret


def HT_SINE(ds, count):
    """Hilbert Transform - SineWave"""
    ret = call_talib_with_ds(ds, count, talib.HT_SINE)
    if ret is None:
        ret = (None, None)
    return ret


def HT_TRENDLINE(ds, count):
    """Hilbert Transform - Instantaneous Trendline"""
    return call_talib_with_ds(ds, count, talib.HT_TRENDLINE)


def HT_TRENDMODE(ds, count):
    """Hilbert Transform - Trend vs Cycle Mode"""
    return call_talib_with_ds(ds, count, talib.HT_TRENDMODE)


def KAMA(ds, count, timeperiod=-2**31):
    """Kaufman Adaptive Moving Average"""
    return call_talib_with_ds(ds, count, talib.KAMA, timeperiod)


def LINEARREG(ds, count, timeperiod=-2**31):
    """Linear Regression"""
    return call_talib_with_ds(ds, count, talib.LINEARREG, timeperiod)


def LINEARREG_ANGLE(ds, count, timeperiod=-2**31):
    """Linear Regression Angle"""
    return call_talib_with_ds(ds, count, talib.LINEARREG_ANGLE, timeperiod)


def LINEARREG_INTERCEPT(ds, count, timeperiod=-2**31):
    """Linear Regression Intercept"""
    return call_talib_with_ds(ds, count, talib.LINEARREG_INTERCEPT, timeperiod)


def LINEARREG_SLOPE(ds, count, timeperiod=-2**31):
    """Linear Regression Slope"""
    return call_talib_with_ds(ds, count, talib.LINEARREG_SLOPE, timeperiod)


def MA(ds, count, timeperiod=-2**31, matype=0):
    """All Moving Average"""
    return call_talib_with_ds(ds, count, talib.MA, timeperiod, matype)


def MACD(ds, count, fastperiod=-2**31, slowperiod=-2**31, signalperiod=-2**31):
    """Moving Average Convergence/Divergence"""
    ret = call_talib_with_ds(ds, count, talib.MACD, fastperiod, slowperiod, signalperiod)
    if ret is None:
        ret = (None, None, None)
    return ret


def MACDEXT(ds, count, fastperiod=-2**31, fastmatype=0, slowperiod=-2**31, slowmatype=0, signalperiod=-2**31, signalmatype=0):
    """MACD with controllable MA type"""
    ret = call_talib_with_ds(ds, count, talib.MACDEXT, fastperiod, fastmatype, slowperiod, slowmatype, signalperiod, signalmatype)
    if ret is None:
        ret = (None, None, None)
    return ret


def MACDFIX(ds, count, signalperiod=-2**31):
    """Moving Average Convergence/Divergence Fix 12/26"""
    ret = call_talib_with_ds(ds, count, talib.MACDFIX, signalperiod)
    if ret is None:
        ret = (None, None, None)
    return ret


def MAMA(ds, count, fastlimit=-4e37, slowlimit=-4e37):
    """MESA Adaptive Moving Average"""
    ret = call_talib_with_ds(ds, count, talib.MAMA, fastlimit, slowlimit)
    if ret is None:
        ret = (None, None)
    return ret


def MAX(ds, count, timeperiod=-2**31):
    """Highest value over a specified period"""
    return call_talib_with_ds(ds, count, talib.MAX, timeperiod)


def MAXINDEX(ds, count, timeperiod=-2**31):
    """Index of highest value over a specified period"""
    return call_talib_with_ds(ds, count, talib.MAXINDEX, timeperiod)


def MEDPRICE(barDs, count):
    """Median Price"""
    return call_talib_with_hl(barDs, count, talib.MEDPRICE)


def MFI(barDs, count, timeperiod=-2**31):
    """Money Flow Index"""
    return call_talib_with_hlcv(barDs, count, talib.MFI, timeperiod)


def MIDPOINT(ds, count, timeperiod=-2**31):
    """MidPoint over period"""
    return call_talib_with_ds(ds, count, talib.MIDPOINT, timeperiod)


def MIDPRICE(barDs, count, timeperiod=-2**31):
    """Midpoint Price over period"""
    return call_talib_with_hl(barDs, count, talib.MIDPRICE, timeperiod)


def MIN(ds, count, timeperiod=-2**31):
    """Lowest value over a specified period"""
    return call_talib_with_ds(ds, count, talib.MIN, timeperiod)


def MININDEX(ds, count, timeperiod=-2**31):
    """Index of lowest value over a specified period"""
    return call_talib_with_ds(ds, count, talib.MININDEX, timeperiod)


def MINMAX(ds, count, timeperiod=-2**31):
    """Lowest and highest values over a specified period"""
    ret = call_talib_with_ds(ds, count, talib.MINMAX, timeperiod)
    if ret is None:
        ret = (None, None)
    return ret


def MINMAXINDEX(ds, count, timeperiod=-2**31):
    """Indexes of lowest and highest values over a specified period"""
    ret = call_talib_with_ds(ds, count, talib.MINMAXINDEX, timeperiod)
    if ret is None:
        ret = (None, None)
    return ret


def MINUS_DI(barDs, count, timeperiod=-2**31):
    """Minus Directional Indicator"""
    return call_talib_with_hlc(barDs, count, talib.MINUS_DI, timeperiod)


def MINUS_DM(barDs, count, timeperiod=-2**31):
    """Minus Directional Movement"""
    return call_talib_with_hl(barDs, count, talib.MINUS_DM, timeperiod)


def MOM(ds, count, timeperiod=-2**31):
    """Momentum"""
    return call_talib_with_ds(ds, count, talib.MOM, timeperiod)


def NATR(barDs, count, timeperiod=-2**31):
    """Normalized Average True Range"""
    return call_talib_with_hlc(barDs, count, talib.NATR, timeperiod)


def OBV(ds1, volumeDs, count):
    """On Balance Volume"""
    data1 = value_ds_to_numpy(ds1, count)
    if data1 is None:
        return None
    data2 = value_ds_to_numpy(volumeDs, count)
    if data2 is None:
        return None
    return talib.OBV(data1, data2)


def PLUS_DI(barDs, count, timeperiod=-2**31):
    """Plus Directional Indicator"""
    return call_talib_with_hlc(barDs, count, talib.PLUS_DI, timeperiod)


def PLUS_DM(barDs, count, timeperiod=-2**31):
    """Plus Directional Movement"""
    return call_talib_with_hl(barDs, count, talib.PLUS_DM, timeperiod)


def PPO(ds, count, fastperiod=-2**31, slowperiod=-2**31, matype=0):
    """Percentage Price Oscillator"""
    return call_talib_with_ds(ds, count, talib.PPO, fastperiod, slowperiod, matype)


def ROC(ds, count, timeperiod=-2**31):
    """Rate of change : ((price/prevPrice)-1)*100"""
    return call_talib_with_ds(ds, count, talib.ROC, timeperiod)


def ROCP(ds, count, timeperiod=-2**31):
    """Rate of change Percentage: (price-prevPrice)/prevPrice"""
    return call_talib_with_ds(ds, count, talib.ROCP, timeperiod)


def ROCR(ds, count, timeperiod=-2**31):
    """Rate of change ratio: (price/prevPrice)"""
    return call_talib_with_ds(ds, count, talib.ROCR, timeperiod)


def ROCR100(ds, count, timeperiod=-2**31):
    """Rate of change ratio 100 scale: (price/prevPrice)*100"""
    return call_talib_with_ds(ds, count, talib.ROCR100, timeperiod)


def RSI(ds, count, timeperiod=-2**31):
    """Relative Strength Index"""
    return call_talib_with_ds(ds, count, talib.RSI, timeperiod)


def SAR(barDs, count, acceleration=-4e37, maximum=-4e37):
    """Parabolic SAR"""
    return call_talib_with_hl(barDs, count, talib.SAR, acceleration, maximum)


def SAREXT(barDs, count, startvalue=-4e37, offsetonreverse=-4e37, accelerationinitlong=-4e37, accelerationlong=-4e37, accelerationmaxlong=-4e37, accelerationinitshort=-4e37, accelerationshort=-4e37, accelerationmaxshort=-4e37):
    """Parabolic SAR - Extended"""
    return call_talib_with_hl(barDs, count, talib.SAREXT, startvalue, offsetonreverse, accelerationinitlong, accelerationlong, accelerationmaxlong, accelerationinitshort, accelerationshort, accelerationmaxshort)


def SMA(ds, count, timeperiod=-2**31):
    """Simple Moving Average"""
    return call_talib_with_ds(ds, count, talib.SMA, timeperiod)


def STDDEV(ds, count, timeperiod=-2**31, nbdev=-4e37):
    """Standard Deviation"""
    return call_talib_with_ds(ds, count, talib.STDDEV, timeperiod, nbdev)


def STOCH(barDs, count, fastk_period=-2**31, slowk_period=-2**31, slowk_matype=0, slowd_period=-2**31, slowd_matype=0):
    """Stochastic"""
    ret = call_talib_with_hlc(barDs, count, talib.STOCH, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)
    if ret is None:
        ret = (None, None)
    return ret


def STOCHF(barDs, count, fastk_period=-2**31, fastd_period=-2**31, fastd_matype=0):
    """Stochastic Fast"""
    ret = call_talib_with_hlc(barDs, count, talib.STOCHF, fastk_period, fastd_period, fastd_matype)
    if ret is None:
        ret = (None, None)
    return ret


def STOCHRSI(ds, count, timeperiod=-2**31, fastk_period=-2**31, fastd_period=-2**31, fastd_matype=0):
    """Stochastic Relative Strength Index"""
    ret = call_talib_with_ds(ds, count, talib.STOCHRSI, timeperiod, fastk_period, fastd_period, fastd_matype)
    if ret is None:
        ret = (None, None)
    return ret


def SUM(ds, count, timeperiod=-2**31):
    """Summation"""
    return call_talib_with_ds(ds, count, talib.SUM, timeperiod)


def T3(ds, count, timeperiod=-2**31, vfactor=-4e37):
    """Triple Exponential Moving Average (T3)"""
    return call_talib_with_ds(ds, count, talib.T3, timeperiod, vfactor)


def TEMA(ds, count, timeperiod=-2**31):
    """Triple Exponential Moving Average"""
    return call_talib_with_ds(ds, count, talib.TEMA, timeperiod)


def TRANGE(barDs, count):
    """True Range"""
    return call_talib_with_hlc(barDs, count, talib.TRANGE)


def TRIMA(ds, count, timeperiod=-2**31):
    """Triangular Moving Average"""
    return call_talib_with_ds(ds, count, talib.TRIMA, timeperiod)


def TRIX(ds, count, timeperiod=-2**31):
    """1-day Rate-Of-Change (ROC) of a Triple Smooth EMA"""
    return call_talib_with_ds(ds, count, talib.TRIX, timeperiod)


def TSF(ds, count, timeperiod=-2**31):
    """Time Series Forecast"""
    return call_talib_with_ds(ds, count, talib.TSF, timeperiod)


def TYPPRICE(barDs, count):
    """Typical Price"""
    return call_talib_with_hlc(barDs, count, talib.TYPPRICE)


def ULTOSC(barDs, count, timeperiod1=-2**31, timeperiod2=-2**31, timeperiod3=-2**31):
    """Ultimate Oscillator"""
    return call_talib_with_hlc(barDs, count, talib.ULTOSC, timeperiod1, timeperiod2, timeperiod3)


def VAR(ds, count, timeperiod=-2**31, nbdev=-4e37):
    """Variance"""
    return call_talib_with_ds(ds, count, talib.VAR, timeperiod, nbdev)


def WCLPRICE(barDs, count):
    """Weighted Close Price"""
    return call_talib_with_hlc(barDs, count, talib.WCLPRICE)


def WILLR(barDs, count, timeperiod=-2**31):
    """Williams' %R"""
    return call_talib_with_hlc(barDs, count, talib.WILLR, timeperiod)


def WMA(ds, count, timeperiod=-2**31):
    """Weighted Moving Average"""
    return call_talib_with_ds(ds, count, talib.WMA, timeperiod)
