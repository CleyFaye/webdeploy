#!/usr/bin/env python3
# encoding=utf-8

from sys import (argv,
                 executable,
                 )
from os import (getuid,
                getgid,
                environ,
                )
from subprocess import call
from wdeploy import (config,
                     runTask,
                     utils,
                     user,
                     )
from logging import getLogger

logg = getLogger(__name__)


def run():
    """Run all tasks from the configuration."""
    for taskId, task in enumerate(config().TASKS):
        logg.info('Running task %s: %s'
                  % (taskId + 1,
                     task['name'],
                     ),
                  )
        runTask(task)


def sudoMe():
    """Rerun self using sudo."""
    try:
        logg.info('Calling sudo to rerun self')
        sudo = utils.which(utils.SUDO)
        callArg = [sudo,
                   '-E',
                   executable,
                   argv[0],
                   ]
        environ[user.ORIGINAL_UID_KEY] = str(getuid())
        environ[user.ORIGINAL_GID_KEY] = str(getgid())
        call(callArg)
    except Exception:
        logg.error('sudo not found; re-run this script as root.')


def main():
    if getuid() != 0:
        logg.warn('This script need to be root to operate correctly')
        sudoMe()
    else:
        run()

if __name__ == '__main__':
    main()
