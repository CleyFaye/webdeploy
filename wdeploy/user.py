# encoding=utf-8
"""Manage user switching"""
from functools import wraps
from os import (seteuid,
                setegid,
                environ,
                getuid,
                getgid,
                )
from os.path import (getmtime,
                     )
from pwd import (getpwnam,
                 getpwuid,
                 )
from grp import (getgrnam,
                 getgrgid,
                 )
from multiprocessing import (Process,
                             SimpleQueue,
                             )
from wdeploy import (config,
                     utils,
                     )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


ORIGINAL_UID_KEY = 'WDEPLOY_ORIGINAL_UID'
ORIGINAL_GID_KEY = 'WDEPLOY_ORIGINAL_GID'


def as_user(userName=None,
            groupName=None,
            ):
    """Return a decorator that run a function as another user.

    Parameters
    ----------
    userName : string | runnable
        The user name (as a string) to run the function as.
        If it is a runnable, it is called when the function is called, and is
        expected to return the user name.
    groupName : string | runnable
        The group name (as a string) to run the function as.
        If it is a runnable, it is called when the function is called, and is
        expected to return the group name.

    Notes
    -----
    The function will be run in a separate process through the multiprocessing
    facilities. Existing open files are still available in this context.
    Return values can be handled, but they have to go through a
    multiprocessing.SimpleQueue object, making it impossible to pass advanced
    objects.
    Exception raised in the function will be re-raised to the caller
    transparently.
    """
    def decorator(function):
        """The real decorator, built using as_user()"""
        @wraps(function)
        def decorated(*args, **kwargs):
            """Wrapped function, change uid and retrieve result."""
            resultQueue = SimpleQueue()

            def user_switched_process(*args, **kwargs):
                """Function called in subprocess."""
                logg.debug('Running function as another user')
                if groupName:
                    if isinstance(groupName, str):
                        realGroupName = groupName
                    else:
                        realGroupName = groupName()
                    logg.debug('Group: %s' % realGroupName)
                    setegid(getgrnam(realGroupName).gr_gid)
                if userName:
                    if isinstance(userName, str):
                        realUserName = userName
                    else:
                        realUserName = userName()
                    logg.debug('User: %s' % realUserName)
                    seteuid(getpwnam(realUserName).pw_uid)
                try:
                    result = function(*args, **kwargs)
                    resultQueue.put(result)
                    resultQueue.put(None)
                except Exception as e:
                    resultQueue.put(None)
                    resultQueue.put(e)

            subprocess = Process(target=user_switched_process,
                                 args=args,
                                 kwargs=kwargs,
                                 )
            subprocess.start()
            subprocess.join()
            result = resultQueue.get()
            exception = resultQueue.get()
            if exception:
                raise exception
            return result
        return decorated
    return decorator


def prefix_user():
    """Return the name of the prefix user as configured in the project"""
    return config().PREFIX_USER


def prefix_group():
    """Return the name of the prefix group as configured in the project"""
    return config().PREFIX_GROUP


def original_user():
    """Return the name of the original user before rerunning the script wit sudo

    Notes
    -----
    If the script was run with sudo manually, this will just return the current
    user (root).
    """
    if ORIGINAL_UID_KEY in environ:
        uid = int(environ[ORIGINAL_UID_KEY])
    else:
        uid = getuid()
    return getpwuid(uid).pw_name


def original_group():
    """Return the name of the original group before running sudo.

    Notes
    -----
    See original_user()
    """
    if ORIGINAL_GID_KEY in environ:
        gid = int(environ[ORIGINAL_GID_KEY])
    else:
        gid = getgid()
    return getgrgid(gid).gr_name


@as_user(original_user, original_group)
def readSourceFile(sourcePath):
    """Return the content of a source file using original user"""
    with open(sourcePath, 'rb') as inFile:
        return inFile.read()


@as_user(prefix_user, prefix_group)
def writeDestinationFile(destinationPath, content):
    """Write a destination file using prefix user"""
    utils.makeParentPath(destinationPath)
    with open(destinationPath, 'wb') as outFile:
        outFile.write(content)


def _getMTime(path):
    """Return a resource mtime, or 0 if the resource doesn't exist"""
    try:
        return getmtime(path)
    except OSError:
        return 0


@as_user(original_user, original_group)
def getSourceMTime(sourcePath):
    """Return a source file mtime"""
    return _getMTime(sourcePath)


@as_user(prefix_user, prefix_group)
def getDestinationMTime(destinationPath):
    """Return a destination file mtime"""
    return _getMTime(destinationPath)


@as_user(original_user, original_group)
def crawlSource(path):
    return list(utils.walkfiles(path))


@as_user(prefix_user, prefix_group)
def crawlDestination(path):
    return list(utils.walkfiles(path))
