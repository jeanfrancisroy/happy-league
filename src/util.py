'''
Created on 2011-11-03

@author: alexandre
'''

from os import path
import cPickle
import fcntl
import datetime
import time as t

def parseTime( time ):
    """
    Extract the number of minutes from a time object or a time string
    """
    if isinstance( time, datetime.time ):
        return 60 * time.hour + time.minute 
    elif isinstance( time, (str,unicode)):
        h,m = time.split(':',1)
        return 60*int(h) + int(m)
    else:
        return time

def unparseTime( time ):
    h = time/60
    m = time - h*60
    return (h,m)


def formatTime(sec, fmt='%H:%M:%S'):
    return t.strftime( fmt, t.localtime(sec))
    
def formatDelay(sec, fmt='%H:%M:%S'):
    return t.strftime( fmt, t.gmtime(sec))


def readFile( *args ):
    """
    A wrapper to simplify file reading
    fileName = path.join(*args)
    If fileName doesn't exist None is returned.
    """
    filePath = path.join( *args )
    if not path.exists( filePath ):
        return None
    with open( filePath, 'r' ) as fd:
        return fd.read() 
    
    
def writePkl( obj, *args, **kwArgs ):
    """
    Serialize an object to file.
    the fileName is path.join(*args)
    """
    pklPath = path.join( *args )
    with open( pklPath, 'w' ) as fd:
        if kwArgs.get('lock',False): fcntl.flock(fd, fcntl.LOCK_EX+ fcntl.LOCK_NB )
        if kwArgs.get('lock_block',False): fcntl.flock(fd, fcntl.LOCK_EX )
        cPickle.dump( obj, fd, cPickle.HIGHEST_PROTOCOL )
        
def readPkl( *args, **kwArgs ):
    """
    Unserialize an object from file.
    the fileName is path.join(*args)
    """
    try:
        with open( path.join( *args ), 'r') as fd: 
#            if kwArgs.get('lock',False): fcntl.flock(fd, fcntl.LOCK_EX+ fcntl.LOCK_NB )
            return cPickle.load(fd)
    except IOError: 
        if kwArgs.has_key('defaultVal'): return kwArgs['defaultVal']
        else: raise
        
        