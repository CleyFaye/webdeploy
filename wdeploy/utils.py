# encoding=utf-8
"""Utility functions for the WebDeploy project.
"""
from codecs import open as codecs_open
import grp
from os import (access,
                chmod,
                chown,
                environ,
                makedirs,
                walk,
                X_OK,
                )
from os.path import (isdir,
                     isfile,
                     join,
                     pathsep,
                     relpath,
                     dirname,
                     )
import pwd
from wdeploy import config
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


MAKE = 'make'
SUDO = 'sudo'
GIT = 'git'

DATA_DIR = '.deploy'


def chowner(path,
            user,
            group,
            ):
    """Change a path owner and group.

    Parameters
    ----------
    path : string
        The resource path
    user : string
        The user name to be the new owner of the resource. Can be None, in which
        case it will not be changed.
    group : string
        The group name to be the new owner of the resource. Can be None, in
        which case it will not be changed.


    Notes
    -----
    Only available on unix systems.
    """
    if user is None and group is None:
        return
    if user:
        uid = pwd.getpwnam(user).pw_uid
    else:
        uid = -1

    if group:
        gid = grp.getgrnam(group).gr_gid
    else:
        gid = -1
    if user and group:
        logg.info('Changing user/group for "%s" to "%s/%s"'
                  % (path,
                     user,
                     group,
                     ),
                  )
    if not group:
        logg.info('Changing user for "%s" to "%s"'
                  % (
                      path,
                      user,
                  ),
                  )
    else:
        logg.info('Changing group for "%s" to "%s"'
                  % (
                      path,
                      group,
                  ),
                  )
    chown(path,
          uid,
          gid,
          )


def cfg_chown(path):
    """Change a resource owner and group according to project configuration."""
    chowner(path,
            config().PREFIX_USER,
            config().PREFIX_GROUP,
            )


def cfg_chmod(path):
    """Change a path permissions according to project configuration."""
    if config().PREFIX_PERMISSIONS:
        logg.info('Changing permissions for "%s" to %s' %
                  (path,
                   config().PREFIX_PERMISSIONS,
                   ),
                  )
        chmod(path,
              int(config().PREFIX_PERMISSIONS,
                  8,
                  ),
              )


def real_mkdir(fullDirPath):
    """Create a directory on the FS.

    Parameters
    ----------
    fullDirPath : string
        The full directory path


    Notes
    -----
    The newly created directory's permissions are set according to the project
    settings.
    """
    if not isdir(fullDirPath):
        logg.info('Creating directory "%s"' % fullDirPath)
        makedirs(fullDirPath)
        cfg_chown(fullDirPath)
        cfg_chmod(fullDirPath)


def makeParentPath(fullPath):
    """Create the directories above the given path.

    Parameters
    ----------
    fullPath : string
        The path to a resource. All parents directories will be created.


    Notes
    -----
    All directories created there will have their permissions set according to
    the project configuration. This behavior is different than real_mkdir().
    """
    directoryPath = dirname(fullPath)
    if isdir(directoryPath):
        return
    makeParentPath(directoryPath)
    real_mkdir(directoryPath)


def open_utf8(fileName, mode):
    """Open all files in UTF-8"""
    return codecs_open(fileName,
                       mode,
                       encoding='utf-8')


def which(toolName):
    """Return the full path to a program based on it's name.

    Parameters
    ----------
    toolName : string
        The basename of a binary.


    Returns
    -------
    Full path to the binary.


    Notes
    -----
    This function will test the following in order:
    * Check for a <toolName>_BIN environment variable. If present, it will use
      it, and fail if the binary isn't available.
    * Check for a <toolName>_PATH environment variable. If present, it will use
      it, and fail if the binary isn't available in this directory.
    * Check the path to find the binary.

    Environment variable are all uppercase.
    Results are cached, meaning if the environment change after the first call
    to find a binary path, these changes won't be reflected here.
    If the tool can't be found, an exception is raised.
    """
    myself = which
    try:
        myself.cache
    except AttributeError:
        myself.cache = {}
    if toolName in myself.cache:
        return myself.cache[toolName]

    binEnviron = '%s_BIN' % toolName.upper()
    pathEnviron = '%s_PATH' % toolName.upper()
    if binEnviron in environ:
        varSrc = binEnviron
        path = environ[varSrc]
    else:
        if pathEnviron in environ:
            varSrc = pathEnviron
            pathCandidates = [environ[varSrc]]
        else:
            varSrc = 'PATH'
            pathCandidates = environ[varSrc].split(pathsep)
        for candidate in pathCandidates:
            path = join(candidate, toolName)
            if isexecutable(path):
                break
    if not isexecutable(path):
        raise Exception('Tool "%s" not found (from %s env. var = %s)' %
                        (toolName,
                         varSrc,
                         environ[varSrc],
                         ),
                        )
    myself.cache[toolName] = path
    return path


def isexecutable(path):
    """Determine if a path point to an executable file."""
    return isfile(path) and access(path, X_OK)


def dataPath():
    """Return a path in the project that can be used to store files.

    Returns
    -------
    A directory suitable for storage of data used by WebDeploy that should not
    pollute the project tree.


    Notes
    -----
    The directory is stored in the root of the project, and will be created if
    required.
    """
    result = join(config().ROOT,
                  DATA_DIR,
                  )
    if not isdir(result):
        logg.info('Creating cache directory "%s"' % result)
        makedirs(result)
    return result


def walkfiles(path):
    """List all files from a given directory.

    Yields
    ------
    This generator returns all files in the form of tuples. First tuple element
    is the file path relative to the path argument, second tuple element is the
    file name.
    """
    for dirPath, _, files in walk(path):
        localPath = relpath(dirPath,
                            path)
        for fileName in files:
            yield (localPath,
                   fileName)
