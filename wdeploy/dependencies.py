# encoding=utf-8
from os.path import (join,
                     isfile,
                     getmtime,
                     )


def _getDependencyFile(dependencyRelPath,
                       allFiles,
                       dependencyFiles,
                       includeDirs,
                       dependencyCheck,
                       ):
    """Update dependencyFiles and return the requested file object"""
    if dependencyRelPath in allFiles:
        return allFiles[dependencyRelPath]
    if dependencyRelPath in dependencyFiles:
        return dependencyFiles[dependencyRelPath]
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
                      dependencyCheck,
                      )
            return newFileObject
    return RuntimeError('Missing dependency: %s' % dependencyRelPath)


def _fillDeps(fileObject,
              allFiles,
              dependencyFiles,
              includeDirs,
              dependencyCheck,
              ):
    """Convert a list of string representing the deps to file objects"""
    dependencies = dependencyCheck(fileObject['fullPath'])
    if not dependencies:
        return
    for dependency in dependencies:
        dependencyFile = _getDependencyFile(dependency,
                                            allFiles,
                                            dependencyFiles,
                                            includeDirs,
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
