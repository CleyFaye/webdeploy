# encoding=utf-8
"""Manage user switching"""
from functools import wraps
from os import (seteuid,
                setegid,
                )
from pwd import getpwnam
from grp import getgrnam
from multiprocessing import (Process,
                             SimpleQueue,
                             )
from wdeploy import config
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


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
                if userName:
                    if isinstance(userName, str):
                        realUserName = userName
                    else:
                        realUserName = userName()
                    logg.debug('User: %s' % realUserName)
                    seteuid(getpwnam(realUserName).pw_uid)
                if groupName:
                    if isinstance(groupName, str):
                        realGroupName = groupName
                    else:
                        realGroupName = groupName()
                    logg.debug('Group: %s' % realGroupName)
                    setegid(getgrnam(realGroupName).gr_gid)
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
