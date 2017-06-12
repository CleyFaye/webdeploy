# encoding=utf-8
from os.path import (join,
                     isfile,
                     getmtime,
                     dirname,
                     splitext,
                     )


def _getDependencyFile(dependencyRelPath,
                       allFiles,
                       dependencyFiles,
                       includeDirs,
                       localInclude,
                       dependencyCheck,
                       ):
    """Update dependencyFiles and return the requested file object"""
    if dependencyRelPath in dependencyFiles:
        return dependencyFiles[dependencyRelPath]
    if includeDirs:
        for includeDir in includeDirs:
            candidatePath = join(includeDir, dependencyRelPath)
            if isfile(join(includeDir, dependencyRelPath)):
                newFileObject = {'modifiedDate': None,
                                 'relativePath': dependencyRelPath,
                                 'fullPath': candidatePath,
                                 'deps': [],
                                 }
                dependencyFiles[dependencyRelPath] = newFileObject
                _fillDeps(newFileObject,
                          allFiles,
                          dependencyFiles,
                          includeDirs,
                          localInclude,
                          dependencyCheck,
                          )
                return newFileObject
    return RuntimeError('Missing dependency: %s' % dependencyRelPath)


def _fillDeps(fileObject,
              allFiles,
              dependencyFiles,
              includeDirs,
              localInclude,
              dependencyCheck,
              ):
    """Convert a list of string representing the deps to file objects"""
    if not dependencyCheck:
        return
    dependencies = dependencyCheck(fileObject['fullPath'])
    if not dependencies:
        return
    if localInclude:
        includeDirs = includeDirs + [dirname(fileObject['fullPath'])]
    for dependency in dependencies:
        dependencyFile = _getDependencyFile(dependency,
                                            allFiles,
                                            dependencyFiles,
                                            includeDirs,
                                            localInclude,
                                            dependencyCheck,
                                            )
        if _checkDependencies(fileObject, dependencyFile):
            raise RuntimeError('Circular dependency: file %s depends '
                               'on itself through %s' %
                               (fileObject['relativePath'],
                                dependencyFile['relativePath']),
                               )
        fileObject['deps'].append(dependencyFile)


def _checkDependencies(firstFile, newDependency):
    """Make sure newDependency doesn't depend on firstFile.

    Returns
    -------
    bool
        True if there is a loop, False otherwise
    """
    for dependency in newDependency['deps']:
        if dependency is firstFile:
            return True
        else:
            return _checkDependencies(firstFile, dependency)
    return False


def _updateMTime(fileObj):
    """Update the modified time of a file object.

    Notes
    -----
    This will use the newest time of both the file itself and all of its
    dependencies if any.
    """
    selfMTime = getmtime(fileObj['fullPath'])
    for dep in fileObj['deps']:
        if dep['modifiedDate'] is None:
            _updateMTime(dep)
        if dep['modifiedDate'] > selfMTime:
            selfMTime = dep['modifiedDate']
    fileObj['modifiedDate'] = selfMTime


def extensionCheck(exts):
    """Return a filter based on file extension for checkDependencies()

    Parameters
    ----------
    exts : string | list(string)
        An extension, or a list of extension, that are valid for the filter.
        Extensions must not include the initial dot; only the extension part.
        To accept file with no extension in their name, pass an empty string.

    Returns
    -------
    runnable
        A runnable suitable to be used as the validityCheck argument for
        checkDependencies()
    """
    if isinstance(exts, str):
        exts = [exts,
                ]

    def runnable(absolutePath):
        _, pathExt = splitext(absolutePath)
        if pathExt.startswith('.'):
            pathExt = pathExt[1:]
        for ext in exts:
            if ext == pathExt:
                return True
        return False
    return runnable
