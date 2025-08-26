'''
Created on 2011-11-03

@author: alexandre
'''
from os import path
import pickle
import datetime
import time as t


def parseTime(time):
    """
    Extract the number of minutes from a time object or a time string
    """
    if isinstance(time, datetime.time):
        return 60 * time.hour + time.minute
    elif isinstance(time, str):
        h, m = time.split(':', 1)
        return 60*int(h) + int(m)
    else:
        return time


def unparseTime(time):
    h = time // 60
    m = time - h*60
    return (h, m)


def formatTime(sec, fmt='%H:%M:%S'):
    return t.strftime(fmt, t.localtime(sec))


def formatDelay(sec, fmt='%H:%M:%S'):
    return t.strftime(fmt, t.gmtime(sec))


def write_pickle(obj, file_name):
    """Serialize an object to file.

    Parameters
    ----------
    obj: object
        The object to serialize.
    file_name: str
        The target file name.

    """
    with open(file_name, 'wb') as fd:
        pickle.dump(obj, fd)


def read_pickle(file_name):
    """Unserialize an object from file.

    """
    with open(path.join(file_name), 'rb') as fd:
        try:
            return pickle.load(fd)
        except EOFError:
            return None, None, None
