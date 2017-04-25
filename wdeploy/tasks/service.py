# encoding=utf-8
"""
Manage system services.
"""
from subprocess import (
        call,
        )

from wdeploy import (
        task,
        utils,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task()
def service(action, serviceName):
    """Perform an action on a system service.

    action can be start, stop, restart...
    """
    try:
        cmd = utils.which('systemctl')
        callArg = [cmd, action, serviceName]
    except Exception:
        cmd = utils.which('service')
        callArg = [cmd, serviceName, action]
    retVal = call(callArg)
    if retVal == 0:
        return
    raise Exception('Error when changing service state: %s => %s' %
                    (serviceName, action))
