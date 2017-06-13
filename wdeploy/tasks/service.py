# encoding=utf-8
"""Manage system services."""
from subprocess import check_call
from wdeploy import (task,
                     utils,
                     )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


@task()
def service(action, serviceName):
    """Perform an action on a system service.

    Notes
    -----
    action can be start, stop, restart...
    This uses systemctl or service, whichever is available.
    """
    logg.info('Performing action "%s" on service "%s"'
              % (action,
                 serviceName,
                 ),
              )
    try:
        cmd = utils.which('systemctl')
        callArg = [cmd,
                   action,
                   serviceName,
                   ]
    except Exception:
        cmd = utils.which('service')
        callArg = [cmd,
                   serviceName,
                   action,
                   ]
    check_call(callArg)
