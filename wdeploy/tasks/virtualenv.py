# encoding=utf-8
"""Reproduce an existing virtualenv"""
from subprocess import check_call
from os.path import (isdir,
                     join,
                     )
from wdeploy import task
from wdeploy.utils import (readProcessOutput,
                           makeParentPath,
                           )
from wdeploy.user import (as_user,
                          prefix_user,
                          prefix_group,
                          original_user,
                          original_group,
                          writeDestinationFile,
                          )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


@as_user(prefix_user, prefix_group)
def _createVirtualEnvironment(outputDir,
                              pythonBin):
    if isdir(outputDir):
        return
    makeParentPath(outputDir)
    args = ['virtualenv']
    if pythonBin:
        args += ['-p', pythonBin]
    args += [outputDir]
    check_call(args)


@as_user(original_user, original_group)
def _getRequirements(sourceDir):
    return readProcessOutput(join(sourceDir,
                                  'bin',
                                  'pip',
                                  ),
                             None,
                             ['freeze'],
                             )


@as_user(prefix_user, prefix_group)
def _get_installed_requirements(outputDir):
    return readProcessOutput(join(outputDir,
                                  'bin',
                                  'pip',
                                  ),
                             None,
                             ['freeze'],
                             )


@as_user(prefix_user, prefix_group)
def _installRequirements(outputDir):
    pipPath = join(outputDir,
                   'bin',
                   'pip',
                   )
    args = [pipPath,
            'install',
            '-U',
            '-r', join(outputDir,
                       'requirements.txt',
                       ),
            ]
    check_call(args)


@task(sourcePathArguments=['sourceDir'],
      destinationPathArguments=['outputDir'],
      )
def virtualenv(sourceDir,
               outputDir,
               pythonBin,
               ):
    """Reproduce a virtualenv found in sourceDir into outputDir.

    Parameters
    ----------
    sourceDir : str
        The path to the source environment. The script will look for
        path/bin/pip.
    outputDir : str
        The path to the copy environment.
    pythonBin : str
        Path to the python binary to use in the copied virtualenv.


    Notes
    -----
    The copied environment is not a 1:1 copy of the source; it merely reproduces
    the list of installed packages.
    """
    _createVirtualEnvironment(outputDir, pythonBin)
    requirements = _getRequirements(sourceDir)
    installed_requirements = _get_installed_requirements(outputDir)
    if requirements == installed_requirements:
        return
    writeDestinationFile(join(outputDir,
                              'requirements.txt',
                              ),
                         requirements)
    _installRequirements(outputDir)
