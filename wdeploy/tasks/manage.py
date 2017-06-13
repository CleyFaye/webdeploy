# encoding=utf-8
"""Call a manage.py command in a virtualenv"""
from subprocess import call
from os import chdir
from os.path import join
from wdeploy import task
from wdeploy.user import (as_user,
                          prefix_user,
                          prefix_group,
                          original_user,
                          original_group,
                          )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


def _runManage(virtualEnv, projectLocation, args):
    chdir(projectLocation)
    pythonPath = join(virtualEnv,
                      'bin',
                      'python',
                      )
    callArgs = [pythonPath,
                'manage.py',
                ] + args
    retVal = call(callArgs)
    if retVal != 0:
        raise RuntimeError('Error when calling manage.py command')


@as_user(prefix_user, prefix_group)
def _runAsPrefix(virtualEnv, projectLocation, args):
    _runManage(virtualEnv, projectLocation, args)


@as_user(original_user, original_group)
def _runAsOriginal(virtualEnv, projectLocation, args):
    _runManage(virtualEnv, projectLocation, args)


@task()
def manage(virtualEnv,
           projectLocation,
           args,
           runAs,
           ):
    """Call a manage.py command for a Django application.

    Parameters
    ----------
    virtualEnv : string
        Path to the virtualenv to use (will look for virtualEnv/bin/activate)
    projectLocation : string
        Location of the manage.py file
    args : list(string)
        Arguments for manage.py
    runAs : string
        Account to run the command as. Can be either 'original' or 'prefix'.
    """
    runAs = runAs.lower()
    if runAs == 'original':
        _runAsOriginal(virtualEnv, projectLocation, args)
    elif runAs == 'prefix':
        _runAsPrefix(virtualEnv, projectLocation, args)
    else:
        raise RuntimeError('Invalid runAs argument (%s)' % runAs)
