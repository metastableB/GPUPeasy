import threading
from datetime import datetime, timedelta

class Logger:

    def __init__(self, fstdout=None, fstderr=None, debug=False):
        self.__stdout = fstdout
        self.__stderr = fstderr
        self.__debug = debug

    def setDebug(self, val):
        self.__debug = val

    def __currentTimeString(self, zone='IST'):
        assert zone in ['IST']
        td = timedelta(hours=5, minutes=30)
        ct = datetime.now() + td
        cts = format(ct, '%d/%b/%Y %H:%M:%S')
        return cts

    def pInfo(self, *args):
        ct = self.__currentTimeString()
        print('[%s] [Info    ]: ' % ct, *args, file=self.__stdout, flush=True)

    def pError(self, *args):
        ct = self.__currentTimeString()
        print('[%s] [Error   ]: ' % ct, *args, file=self.__stderr, flush=True)

    def pCritical(self, *args):
        ct = self.__currentTimeString()
        print('[%s] [Critical]: ' % ct, *args, file=self.__stderr, flush=True)

    def pWarn(self, *args):
        ct = self.__currentTimeString()
        print('[%s] [Warning ]: ' % ct, *args, file=self.__stdout, flush=True)

    def pSuccess(self, *args):
        ct = self.__currentTimeString()
        print('[%s] [Success ]: ' % ct, *args, file=self.__stdout, flush=True)

    def pDebug(self, *args):
        if not self.__debug:
            return
        ct = self.__currentTimeString()
        print('[%s] [Debug   ]: ' % ct, *args, file=self.__stdout, flush=True)


class LockedList:
    def __init__(self):
        self.__container = list()
        self.__mutex = threading.Lock()

    def lock(self):
        self.__mutex.acquire()

    def release(self):
        self.__mutex.release()

    def append(self, elem):
        self.__mutex.acquire()
        self.__container.append(elem)
        self.__mutex.release()

    def pop(self):
        val = None
        self.__mutex.acquire()
        if len(self.__container) != 0:
            val = self.__container[0]
            del self.__container[0]
        self.__mutex.release()
        return val

    def push(self, elem):
        self.append(elem)

    def __getitem__(self, key):
        self.__mutex.acquire()
        val = self.__container[key]
        self.__mutex.release()
        return val

    def __setitem__(self, key, value):
        self.__mutex.acquire()
        self.__container[key] = value
        self.__mutex.release()

    def __len__(self):
        return len(self.__container)

    def __delitem__(self, key):
        self.__mutex.acquire()
        del self.__container[key]
        self.__mutex.release()

    def getCurrVals(self, unsafe=False):
        '''
        The unsafe option returns a copy of the internal compiler without
        acquiring lock on it. The behaviour of this option in the general case
        is undefined. The only reason to use this is when the lock has been
        acquired through the self.lock() method externally.
        '''
        if unsafe:
            return list(self.__container)
        self.__mutex.acquire()
        val = list(self.__container)
        self.__mutex.release()
        return val

    def deleteValue(self, key, unsafe=False):
        '''
        The unsafe option deletes the element with key without acquiring lock
        on it. The behaviour of this option in the general case is undefined.
        The only reason to use this is when the lock has been acquired through
        the self.lock() method externally.
        '''
        if not unsafe:
            self.__delitem__(key)
            return
        del self.__container[key]
        return
