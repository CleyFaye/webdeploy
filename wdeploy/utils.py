# encoding=utf-8
"""
Utility functions for deploy.py script.
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
import subprocess
from os.path import (isdir,
                     isfile,
                     join,
                     pathsep,
                     relpath,
                     getmtime,
                     )
import pwd
import platform

from wdeploy import (config,
                     dependencies,
                     )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')

MAKE = 'make'
SUDO = 'sudo'
GIT = 'git'

DATA_DIR = '.deploy'


def chowner(path, user, group):
    """Change a path owner and group.

    user and group can be None, in which case they are not changed.
    Note: availability = not windows
    """
    if user:
        uid = pwd.getpwnam(user).pw_uid
    else:
        uid = -1
    if group:
        gid = grp.getgrnam(group).gr_gid
    else:
        gid = -1
    chown(path, uid, gid)


def cfg_chown(path):
    """Change a path owner and group according to project configuration.
    """
    chowner(path, config().PREFIX_USER, config().PREFIX_GROUP)


def cfg_chmod(path):
    """Change a path permissions according to project configuration.
    """
    if config().PREFIX_PERMISSIONS:
        chmod(path, int(config().PREFIX_PERMISSIONS, 8))


def real_mkdir(fullDirPath):
    """Create a directory on the FS.

    This takes as input a full, preferably absolute path.
    The newly created directory's access rights are set according to the
    project settings.
    """
    if not isdir(fullDirPath):
        makedirs(fullDirPath)
        cfg_chown(fullDirPath)
        cfg_chmod(fullDirPath)


def open_utf8(fileName, mode):
    """Open all files in UTF-8"""
    return codecs_open(fileName, mode, encoding='utf-8')


def isToolPresent(toolName):
    try:
        which(toolName)
        return True
    except RuntimeError:
        return False


def which(toolName):
    """Return the full path to a program based on it's name.

    This function will test the following in order:
    * Check for a <toolName>_BIN environment variable. If present, it will use
      it, and fail if the binary isn't available.
    * Check for a <toolName>_PATH environment variable. If present, it will use
      it, and fail if the binary isn't available in this directory.
    * Check the path to find the binary.

    Environment variable are all uppercase.

    It will return the full path to the binary. Results are cached.
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
        toolBinName = binName(toolName)
        if pathEnviron in environ:
            varSrc = pathEnviron
            pathCandidates = [environ[varSrc]]
        else:
            varSrc = 'PATH'
            pathCandidates = environ[varSrc].split(pathsep)
        for candidate in pathCandidates:
            path = join(candidate, toolBinName)
            if isexecutable(path):
                break
    if not isexecutable(path):
        raise RuntimeError('Tool "%s" not found (from %s env. var = %s)' %
                           (toolName,
                            varSrc,
                            environ[varSrc]))
    myself.cache[toolName] = path
    return path


def binName(path):
    """Add the .exe suffix on windows.

    This is not futureproof and most likely to break, if it isn't already.
    """
    if platform.system()[0:3] == 'Win':
        return '%s.exe' % path
    else:
        return path


def isexecutable(path):
    """Determine if a path point to an executable file."""
    return isfile(path) and access(path, X_OK)


def dataPath():
    """
    Return a path in the project that can be used to store temporary
    files.

    Will create the directory if required.
    """
    result = join(config().ROOT, DATA_DIR)
    if not isdir(result):
        makedirs(result)
    return result


def walkfiles(path):
    """List all files from a given directory.

    This generator returns all files in the form of tuples. First tuple element
    is the file path relative to the path argument, second tuple element is the
    file name.
    """
    for dirPath, _, files in walk(path):
        localPath = relpath(dirPath, path)
        for fileName in files:
            yield (localPath, fileName)


def checkDependencies(baseDir,
                      includeDirs,
                      localInclude,
                      validityCheck,
                      dependencyCheck,
                      outputCB,
                      updateCB,
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

    Returns
    -------
    list(string)
        Return the list of all files that were checked by this call. This list
        is made of absolute path.
    """
    sourceFilesPath = walkfiles(baseDir)
    allFiles = {x[0]: {'modifiedDate': None,
                       'relativePath': x[0],
                       'fullPath': join(baseDir, x[0]),
                       'deps': [],
                       }
                for x in sourceFilesPath
                if validityCheck(join(baseDir, x[0]))
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
