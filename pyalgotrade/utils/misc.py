import base64
import sys
import threading
import traceback
import zlib

import pyalgotrade.logger

logger = pyalgotrade.logger.getLogger(__name__)


bugart = '''
       / .'
 .---. \/
(._.' \()
 ^"""^"
BUG!!!
'''


def pyGo(func, *args):
    t = threading.Thread(target=func, daemon=True, args=args)
    t.start()
    return t


def protected_function(exception_rtn=None):
    def wrapper_outter(func):
        def wrapper(*args, **kwargs):
            try:
                rtn = func(*args, **kwargs)
                return rtn
            except Exception:
                info = traceback.format_exc()
                logger.error('-' * 60)
                logger.error(bugart + '\n' + info)
                logger.error('-' * 60)
                return exception_rtn
            except KeyboardInterrupt:
                logger.info('KeyboardInterrupt received, terminating...')
                sys.exit(0)
        return wrapper
    return wrapper_outter


if __name__ == '__main__':
    @protected_function(1)
    def test(num):
        raise Exception(str(num))

    print('we got %s' % str(test(3)))
