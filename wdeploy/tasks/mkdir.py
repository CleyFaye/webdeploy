# encoding=utf-8
"""
Create new directories.
"""
from wdeploy import (
        task,
        utils,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task(destinationPathArguments=['dirName'])
def mkdir(dirName):
    """Create a directory in PREFIX with appropriate access rights.
    """
    utils.real_mkdir(dirName)
