# encoding=utf-8
"""Create symbolic links"""
from os import (symlink,
                readlink,
                )
from os.path import (isfile,
                     islink,
                     join,
                     )
from wdeploy import (config,
                     task,
                     )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


FILE_ALREADY_EXIST_MSG = ('Can\'t create symbolic link: destination already '
                          + 'exist "%s"'
                          )
DIFFERENT_LINK_EXIST_MSG = ('Symbolic link "%s" already exist but point to a '
                            + 'different file'
                            )


@task(destinationPathArguments='source')
def create_symlink(source, destination):
    """Create a symbolic link (if it doesn't exist already) outside of PREFIX.

    Parameters
    ----------
    source : string
        The path (relative to project's PREFIX) of a resource.
    destination : string
        The absolute path where to place the symbolic link
    """
    sourceFullPath = join(config().PREFIX, source)
    if isfile(destination) or islink(destination):
        if not islink(destination):
            raise Exception(FILE_ALREADY_EXIST_MSG % destination)
        if readlink(destination) != sourceFullPath:
            # TODO This might not be true because of relative path
            raise Exception(DIFFERENT_LINK_EXIST_MSG % destination)
        return
    logg.info('Creating symbolic link "%s" => "%s"' % (destination,
                                                       sourceFullPath,
                                                       ),
              )
    symlink(sourceFullPath,
            destination)
