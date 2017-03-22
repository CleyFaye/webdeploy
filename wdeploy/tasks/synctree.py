# encoding=utf-8
"""
synctree task.
Make a mirror of a given directory into another directory.
"""
from fnmatch import (
        fnmatch,
        )
from os import (
        remove,
        rmdir,
        walk,
        )
from os.path import (
        join,
        isfile,
        getmtime,
        )
from shutil import (
        copy,
        )

from wdeploy import (
        config,
        task,
        utils,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task
def synctree(sourceDir, destDir, deleteStalledFiles=True):
    """Synchronize the destination directory with the source directory.

    Any file in the destination directory not found in source will be deleted.
    """
    rsync(
            join(config().ROOT, sourceDir),
            join(config().PREFIX, destDir),
            deleteStalledFiles)


def copyfile(sourcePath, destPath):
    """Copy a file, changing the destination ownership.

    The destination file will have it's owner, group and rights taken from the
    config.
    """
    copy(sourcePath, destPath)
    utils.cfg_chown(destPath)
    utils.cfg_chmod(destPath)


def rsync(
        sourceDir,
        destinationDir,
        deleteStalledFiles,
        excludeList=None):
    """Synchronize files from source to destination (mirror mode).

    If it does not exist, destinationDir will be created.
    The excludeList argument is a list of exclusion patterns that will not be
    copied to destinationDir. File fitting this pattern will however be deleted
    from destination.
    """

    if excludeList is None:
        excludeList = ['*.pyc']
    utils.real_mkdir(destinationDir)

    # List used to delete stall files
    sourceFiles = []

    for relativePath, fileName in utils.walkfiles(sourceDir):
        sourceFiles.append(join(relativePath, fileName))

        destinationPath = join(destinationDir, relativePath)
        destinationFilePath = join(destinationPath, fileName)
        utils.real_mkdir(destinationPath)

        excluded = False
        for exclude in excludeList:
            if fnmatch(fileName, exclude):
                excluded = True
                break
        if excluded:
            continue

        sourceFilePath = join(sourceDir, relativePath, fileName)
        if (isfile(destinationFilePath)
                and getmtime(sourceFilePath) <= getmtime(destinationFilePath)):
            continue

        copyfile(sourceFilePath, destinationFilePath)

    if deleteStalledFiles:
        for relativePath, fileName in utils.walkfiles(destinationDir):
            relativeFilePath = join(relativePath, fileName)
            if relativeFilePath in sourceFiles:
                continue

            destinationFilePath = join(destinationDir, relativeFilePath)
            remove(destinationFilePath)

        for directory, dirs, files in walk(destinationDir, topdown=False):
            if not dirs and not files:
                rmdir(directory)
