#state machine
import enum
import inspect
import sys

import pyalgotrade.logger


logger = pyalgotrade.logger.getLogger(__name__)


def state(state_enum, is_initial_state=False):
    def wrapper(func):
        ''' decorator for state machine
        '''
        assert callable(func)
        assert isinstance(state_enum, enum.Enum)
        func.__state__ = state_enum
        if is_initial_state:
            func.__initial_state__ = True
        return func
    return wrapper


class StateMachine(object):
    ''' new state machine
    '''

    def __init__(self):
        self.__states = {}
        self.__current_state = None
        self.__last_state = None
        initial_set = False
        methods = inspect.getmembers(self.__class__,
                                     predicate=lambda x: (inspect.isfunction(x) or
                                               inspect.ismethod(x)))
        for i in methods:
            if hasattr(i[1], '__state__'):
                self.__register_state(i[1].__state__, getattr(self, i[0]))
            if hasattr(i[1], '__initial_state__'):
                if initial_set:
                    raise Exception('you can only have one initial state')
                initial_set = True
                self.__set_initial_state(i[1].__state__)
        if not initial_set:
            raise Exception('no initial state defined')

    def __register_state(self, name, function):
        logger.debug('Registering state [%s]' % name)
        if name in self.__states:
            raise Exception("Duplicate state %s" % name)
        self.__states[name] = function

    def __set_initial_state(self, name):
        assert name in self.__states
        logger.debug('Initial state [%s]' % name)
        self.__current_state = name

    @property
    def current_state(self):
        return self.__current_state

    @current_state.setter
    def current_state(self, new_state):
        assert new_state in self.__states
        logger.info('Setting state from '
            '[{}] to [{}]'.format(self.__current_state, new_state))
        self.__current_state = new_state

    @property
    def last_state(self):
        return self.__last_state

    def run(self, *args, **kwargs):
        assert self.__current_state is not None
        new_state = self.__states[self.__current_state](*args, **kwargs)
        self.__last_state = self.__current_state
        if new_state != self.__current_state:
            logger.debug('Switch state [%s] -> [%s]' % (self.__current_state,
                                                        new_state))
        assert new_state in self.__states
        self.__current_state = new_state

    def run_forever(self, *args, **kwargs):
        while True:
            self.run(*args, **kwargs)


class StrategyFSM(StateMachine):
    ''' state machine used by strategy runner
        each state should have 2 arguments.
        The first one is "bars" and the second
        one is "states"
    '''

    def __init__(self, barfeed, states):
        super(StrategyFSM, self).__init__()
        self.__barfeed = barfeed
        self.__states = states

    @property
    def barfeed(self):
        return self.__barfeed

    @property
    def state(self):
        return self.__states
