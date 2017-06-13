# encoding=utf-8
""" Run makefiles"""
from os import chdir
from os.path import (abspath,
                     basename,
                     dirname,
                     )
from subprocess import check_call
from wdeploy import (config,
                     task,
                     utils,
                     )
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


@as_user(prefix_user, prefix_group)
def _runAsPrefix(script, target, args):
    _runMakefile(script, target, args)


@as_user(original_user, original_group)
def _runAsOriginal(script, target, args):
    _runMakefile(script, target, args)


def _runMakefile(script, target, args):
    makefileDir = abspath(dirname(script))
    chdir(makefileDir)
    callArg = [utils.which(utils.MAKE),
               '-f', basename(script),
               target]
    if args:
        callArg += ['%s=%s' % (key,
                               args[key].replace(' ', '\\ '),
                               )
                    for key in args]
    check_call(callArg)


@task(sourcePathArguments=['script'])
def makefile(script, target, args, runAs):
    """Run a Makefile.

    Parameters
    ----------
    script : string
        Path to the makefile, relative to the project's root
    target : string
        Makefile target
    args : dict
        Makefile variables, provided as a key=value arguments to make
    runAs : string
        Indicate under which account the makefile should run. Can be one of the
        following : 'root', 'original', 'prefix'. You should make sure that the
        requested account have access to the actual Makefile and its directory.
    """
    runAs = runAs.lower()
    if runAs == 'root':
        func = _runMakefile
    elif runAs == 'prefix':
        func = _runAsPrefix
    elif runAs == 'original':
        func = _runAsOriginal
    else:
        raise RuntimeError('Unknown runAs argument (%s)' % runAs)
    logg.info('Running make script "%s" as "%s"' % (script,
                                                    runAs,
                                                    ),
              )
    func(script, target, args)
