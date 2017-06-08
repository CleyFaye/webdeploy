# encoding=utf-8
"""Create new directories."""
from wdeploy import (task,
                     utils,
                     )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


@task(destinationPathArguments=['dirName'])
def mkdir(dirName):
    """Create a directory in PREFIX with appropriate access rights."""
    logg.info('Creating directory %s' % dirName)
    utils.real_mkdir(dirName)
