# encoding=utf-8
"""
Create symbolic links
"""
from os import (
        symlink,
        readlink,
        )
from os.path import (
        isfile,
        islink,
        join,
        )

from wdeploy import (
        config,
        task,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task
def create_symlink(source, destination):
    """Create a symbolic link (if it doesn't exist already).

    source is relative to the PREFIX, but not destination.
    """
    sourceFullPath = join(config().PREFIX, source)
    if isfile(destination) or islink(destination):
        if not islink(destination):
            raise Exception(
                ('Can\'t create symbolic link: destination already ' +
                 'exist "%s"') % destination)
        if readlink(destination) != sourceFullPath:
            # TODO This might not be true because of relative path
            raise Exception(
                ('Symbolic link "%s" already exist but point to a different ' +
                 'file') % destination)
        return
    symlink(sourceFullPath, destination)
