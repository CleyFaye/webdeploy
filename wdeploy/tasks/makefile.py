# encoding=utf-8
""" Run makefiles"""
from os import chdir
from os.path import (abspath,
                     basename,
                     dirname,
                     )
from subprocess import call
from wdeploy import (config,
                     task,
                     utils,
                     )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


@task(sourcePathArguments=['script'])
def makefile(script, target, args, runAsRoot):
    """Run a Makefile.

    Parameters
    ----------
    script : string
        Path to the makefile, relative to the project's root
    target : string
        Makefile target
    args : dict
        Makefile variables, provided as a key=value arguments to make
    runAsRoot : bool
        If the makefile should run as root. If False, sudo will be used to run
        as the user indicated in the project configuration
    """
    makefileDir = abspath(dirname(script))
    chdir(makefileDir)
    if runAsRoot:
        logg.info('Running make script "%s" as root' % script)
        callArg = []
    else:
        logg.info('Running make script "%s" as "%s"' % (script,
                                                        config().PREFIX_USER,
                                                        ),
                  )
        user = config().PREFIX_USER
        if user:
            callArg = [utils.which(utils.SUDO), '-u', user]
    callArg += [utils.which(utils.MAKE),
                '-f', basename(script),
                target]
    callArg += ['%s=%s' % (key,
                           args[key].replace(' ', '\\ '))
                for key in args]
    retVal = call(callArg)
    if retVal == 0:
        return
    raise Exception('An error occured while running Makefile %s'
                    % script)
