import threading
import json
import coloredlogs
import pyalgotrade.logger


logger = pyalgotrade.logger.getLogger('strategystate')


class StrategyState:

    def __init__(self):
        super(StrategyState, self).__setattr__('__states', {})
        super(StrategyState, self).__setattr__('__state_lock', threading.Lock())

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __getitem__(self, key):
        state_lock = getattr(self, '__state_lock')
        states = getattr(self, '__states')
        state_lock.acquire()
        if key in states:
            rtn =  states[key]
        else:
            rtn = None
        state_lock.release()
        return rtn

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        state_lock = getattr(self, '__state_lock')
        states = getattr(self, '__states')
        state_lock.acquire()
        states[key] = value
        state_lock.release()

    def dumps(self):
        ''' dump object to string
        '''
        self.__state_lock.acquire()
        obj = self.__states.copy()
        self.__state_lock.release()
        return json.dumps(obj)

    def loads(self, data):
        ''' load state object from string
        '''
        obj = json.loads(data)
        self.__state_lock.acquire()
        self.__states = obj
        self.__state_lock.release()

    def __str__(self):
        state_lock = getattr(self, '__state_lock')
        states = getattr(self, '__states')
        state_lock.acquire()
        tmp = states.copy()
        state_lock.release()
        return json.dumps(tmp)


if __name__ == '__main__':
    a = StrategyState()
    a.test = 1
    logger.info(a['test'])
    a['test2'] = 2
    logger.info(a.test2)