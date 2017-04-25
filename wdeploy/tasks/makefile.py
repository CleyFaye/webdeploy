# encoding=utf-8
"""
Run makefiles
"""
from os import (
        chdir,
        )
from os.path import (
        abspath,
        basename,
        dirname,
        join,
        )
from subprocess import (
        call,
        )

from wdeploy import (
        config,
        task,
        utils,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task(sourcePathArguments=['script'])
def makefile(script, target, args, runAsRoot):
    """Run a Makefile.

    This will run the makefile given in script, from the script directory.
    Argument are provided to the makefile as key=pair arguments.

    The Makefile path is relative to ROOT.

    If runAsRoot is False, the script will be run as the user in the
    PREFIX_USER config.
    """
    makefileDir = abspath(dirname(script))
    chdir(makefileDir)
    if runAsRoot:
        callArg = []
    else:
        user = config().PREFIX_USER
        if user:
            callArg = [utils.which(utils.SUDO), '-u', user]
    callArg += [utils.which(utils.MAKE), '-f', basename(script), target]
    callArg += ['%s=%s' % (key, args[key].replace(' ', '\\ ')) for key in args]
    retVal = call(callArg)
    if retVal == 0:
        return
    raise Exception('An error occured while running Makefile %s'
                    % script)
