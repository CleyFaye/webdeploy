#!/usr/bin/env python
# encoding=utf-8

from sys import argv
from os import (
        getuid,
        )
from subprocess import call

from wdeploy import (
        config,
        runTask,
        utils,
        )


def run():
    for taskId, task in enumerate(config().TASKS):
        print('Running task %s: %s' % (taskId + 1, task[0]))
        runTask(task)


def sudoMe():
    try:
        sudo = utils.which(utils.SUDO)
        callArg = [sudo, '-E', 'python', argv[0]]
        call(callArg)
    except Exception as e:
        print('sudo not found; re-run this script as root.')
        print(e)


def main():
    if getuid() != 0:
        print('This script need to be root to operate correctly')
        print('Attempting to re-run the script with sudo')
        sudoMe()
    else:
        run()

if __name__ == '__main__':
    main()
