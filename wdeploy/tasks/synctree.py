# encoding=utf-8
"""Make a mirror of a given directory into another directory."""
from fnmatch import fnmatch
from os import (remove,
                rmdir,
                walk,
                )
from os.path import join
from wdeploy import (task,
                     utils,
                     )
from wdeploy.user import (readSourceFile,
                          writeDestinationFile,
                          getSourceMTime,
                          getDestinationMTime,
                          crawlSource,
                          crawlDestination,
                          )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


@task(sourcePathArguments=['sourceDir'],
      destinationPathArguments=['destDir'],
      )
def synctree(sourceDir,
             destDir,
             deleteStalledFiles=True,
             excludePatterns=None,
             ):
    """Synchronize the destination directory with the source directory.

    Parameters
    ----------
    sourceDir : string
        Source tree to copy, relative to ROOT
    destDir : string
        Destination to copy the tree, relative to PREFIX
    deleteStalledFiles : bool
        Delete files in destination that didn't come from a file in source
    excludePatterns : list(string)
        List of patterns to exclude from the mirror.


    Notes
    -----
    Any file in the destination directory not found in source will be deleted
    unless deleteStalledFiles is False
    """
    logg.info('Mirroring %s into %s'
              % (sourceDir,
                 destDir,
                 ),
              )
    rsync(sourceDir,
          destDir,
          deleteStalledFiles,
          excludePatterns,
          )


def copyfile(sourcePath,
             destPath,
             ):
    """Copy a file, changing the destination ownership.

    Parameters
    ----------
    sourcePath : string
        Full path of the source file
    destPath : string
        Full path of the destination file


    Notes
    -----
    The destination file will have it's owner, group and rights set from the
    config.
    """
    logg.debug('Copying files (%s => %s)'
               % (sourcePath,
                  destPath,
                  ),
               )
    writeDestinationFile(destPath,
                         readSourceFile(sourcePath),
                         )


def rsync(sourceDir,
          destinationDir,
          deleteStalledFiles,
          excludeList=None,
          ):
    """Synchronize files from source to destination (mirror mode).

    Parameters
    ----------
    sourceDir : string
        The source path to mirror
    destinationDir : string
        The place to mirror sourceDir into
    deleteStalledFiles : bool
        Delete files in destination that have no source in source
    excludeList : list(string)
        List of patterns for file that should not be copied
        Files fitting this pattern will however be deleted from destination.


    Notes
    -----
    If it does not exist, destinationDir will be created.
    The patternd for excludeList are the same as with fnmatch()
    If deleteStalledFiles is True, empty directories in the destination path
    will also be removed.
    """
    utils.real_mkdir(destinationDir)

    # List used to delete stall files
    sourceFiles = []

    for relativePath, fileName in crawlSource(sourceDir):
        excluded = False
        if excludeList:
            for exclude in excludeList:
                if fnmatch(fileName, exclude):
                    excluded = True
                    break
            if excluded:
                continue

        sourceFiles.append(join(relativePath,
                                fileName))

        destinationFilePath = join(destinationDir,
                                   relativePath,
                                   fileName)

        sourceFilePath = join(sourceDir,
                              relativePath,
                              fileName)
        destinationTime = getDestinationMTime(destinationFilePath)
        sourceTime = getSourceMTime(sourceFilePath)
        if (sourceTime <= destinationTime):
            continue

        copyfile(sourceFilePath,
                 destinationFilePath)

    if deleteStalledFiles:
        for relativePath, fileName in crawlDestination(destinationDir):
            relativeFilePath = join(relativePath,
                                    fileName)
            if relativeFilePath in sourceFiles:
                continue

            destinationFilePath = join(destinationDir,
                                       relativeFilePath)
            logg.debug('Removing stale file %s' % destinationFilePath)
            remove(destinationFilePath)

        for directory, dirs, files in walk(destinationDir,
                                           topdown=False):
            if not dirs and not files:
                logg.debug('Removing stale directory %s' % directory)
                rmdir(directory)
