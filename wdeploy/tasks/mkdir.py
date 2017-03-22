# encoding=utf-8
"""
Create new directories.
"""
from os.path import (
        join,
        )
from wdeploy import (
        config,
        task,
        utils,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task
def mkdir(dirName):
    """Create a directory in PREFIX with appropriate access rights.
    """
    fullDirPath = join(config().PREFIX, dirName)
    utils.real_mkdir(fullDirPath)
