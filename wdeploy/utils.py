# encoding=utf-8
"""Utility functions for the WebDeploy project."""
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
import subprocess
from os.path import (isdir,
                     isfile,
                     join,
                     pathsep,
                     relpath,
                     dirname,
                     getmtime,
                     )
import pwd
from wdeploy import (config,
                     dependencies,
                     )
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


def isToolPresent(toolName):
    try:
        which(toolName)
        return True
    except RuntimeError:
        return False


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
        raise RuntimeError('Tool "%s" not found (from %s env. var = %s)' %
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
            yield localPath, fileName


def checkDependencies(baseDir,
                      includeDirs,
                      localInclude,
                      validityCheck,
                      dependencyCheck,
                      outputCB,
                      updateCB,
                      filesList=None,
                      ):
    """Crawl a directory to find updated files.

    Parameters
    ----------
    baseDir : string
        The base directory, containing potentially updated files.
        Only files from this directory (and subdirectory) might be returned by
        checkDependencies().
    includeDirs : list(string)
        A list of extra directories to check for include files. These files will
        be used to check if a file in baseDir needs to be rebuilt or not, but
        they will not be returned by checkDependencies().
    localInclude : bool,
        Indicate if the include dir list should also have the current file's
        directory appended to it.
    validityCheck : runnable
        A runnable that will receive an absolute file path as its only
        argument, and must return either True if the file is valid or False
        otherwise.
    dependencyCheck : runnable
        A runnable that will receive an absolute file path as its only
        argument, and must return the list of dependency as a list of relative
        file path.
        This runnable can also return None in case there are no dependencies.
    outputCB : runnable
        A runnable that will receive a relative file path, and must return the
        absolute file path where the corresponding output file is located.
        This is required, as it is the only way for checkDependencies() to check
        modification times on both input/dependencies and output.
    updateCB : runnable
        A runnable that will receive two arguments: the absolute file name of a
        source file (in baseDir) and the absolute file name of the destination
        file (as returned by outputCB).
        This runnable is only called when a file need updating.
    filesList : list(string) (optional)
        A list of relative path to crawl from the source directory. If not
        provided, all files are checked.

    Returns
    -------
    list(string)
        Return the list of all files that were checked by this call. This list
        is made of absolute path.
    """
    if filesList is None:
        sourceFilesPath = walkfiles(baseDir)
        filesList = [join(x[0], x[1])
                     for x in sourceFilesPath
                     ]
    allFiles = {x: {'modifiedDate': None,
                       'relativePath': x,
                       'fullPath': join(baseDir, x),
                       'deps': [],
                       }
                for x in filesList
                if validityCheck(join(baseDir, x))
                }
    dependencyFiles = {}

    for fileObj in allFiles:
        dependencies._fillDeps(fileObj,
                               allFiles,
                               dependencyFiles,
                               includeDirs,
                               localInclude,
                               dependencyCheck,
                               )

    output = []
    for fileObj in allFiles:
        outputPath = outputCB(fileObj['relativePath'])
        output.append(outputPath)
        dependencies._updateMTime(fileObj)
        outputMDate = getmtime(outputPath)
        if outputMDate <= fileObj['modifiedDate']:
            updateCB(fileObj['fullPath'],
                     outputPath,
                     )
    return output


def pipeRun(binaryName,
            inputStream,
            args):
    """Run a program, providing input as the standard input.

    Parameters
    ----------
    binaryName : string
        Name of the program to run. This will be passed as-is to which()
    inputStream : file
        Source for the program standard input. Can be None.
    args : list
        List of arguments to pass to the program


    Returns
    -------
    process
        The process


    Notes
    -----
    The value returned is a Popen object, where stdout is PIPEd, and stderr
    silenced.
    Since stdout is using a pipe in the child process, caller is responsible of
    reading from it. If not read, the child process might block when writing.
    """
    args = [which(binaryName)] + args
    result = subprocess.Popen(args,
                              stdin=inputStream or subprocess.DEVNULL,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL,
                              )
    return result
