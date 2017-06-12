# encoding=utf-8
from os.path import (join,
                     splitext,
                     )
from os import (unlink,
                )
from wdeploy import (task,
                     utils,
                     )
from wdeploy.user import (as_user,
                          original_user,
                          original_group,
                          writeDestinationFile,
                          )
from wdeploy.dependencies import extensionCheck

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


def _jpgProcess(sourceFile):
    """Return a process that minify an input jpeg file"""
    if utils.isToolPresent('jpegtran'):
        args = ['-optimize',
                '-progressive',
                '-copy', 'none',
                ]
        return utils.pipeRun('jpegtran', sourceFile, args)
    raise RuntimeError('No JPG minification facilities present!'
                       + '(tried jpegtran)')


def _pngProcess(sourceFile):
    """Return a process that minify an input PNG file"""
    if utils.isToolPresent('pngcrush_wrapper'):
        args = []
        return utils.pipeRun('pngcrush_wrapper', sourceFile, args)
    raise RuntimeError('No PNG minification facilities present!'
                       + '(tried pngcrush_wrapper)')


def _svgProcess(sourceFile):
    """Return a process that minify an input SVG file"""
    if utils.isToolPresent('svgo'):
        args = ['-i', '-',
                '-o', '-',
                '--multipass',
                ]
        return utils.pipeRun('svgo', sourceFile, args)
    raise RuntimeError('No SVG minification facilities present!'
                       + '(tried svgo)')


@as_user(original_user, original_group)
def _imgProcessFromSource(source):
    """Read and process a source image file

    Returns
    -------
    string
        The processed file content
    """
    _, ext = splitext(source)
    ext = ext.lower()
    if ext == 'png':
        method = _pngProcess
    elif ext == 'jpg':
        method = _jpgProcess
    elif ext == 'svg':
        method = _svgProcess
    else:
        raise RuntimeError('Unknown image extension: %s' % ext)
    with utils.open(source, 'rb') as inFile:
        proc = method(inFile)
        return proc.read()


def imgProcess(source, dest):
    """Process an image file into a minified image file"""
    writeDestinationFile(dest,
                         _imgProcessFromSource(source),
                         )


@task(sourcePathArguments=['sourceDir', 'includeDirs'],
      destinationPathArguments=['destinationDir'],
      )
def img(sourceDir,
        destinationDir,
        removeStale=True):
    """Process all image files from sourceDir.

    This task will look for changes in the source directory, and process/copy
    files in the destination directory.

    It will handle jpg, png and svg files.
    """
    def outputCB(relativePath):
        return join(destinationDir, relativePath)

    def updateCB(absoluteSource, absoluteDest):
        imgProcess(absoluteSource,
                   absoluteDest,
                   )

    outputFiles = utils.checkDependencies(baseDir=sourceDir,
                                          includeDirs=None,
                                          localInclude=True,
                                          validityCheck=extensionCheck(['png',
                                                                        'svg',
                                                                        'jpg',
                                                                        ]),
                                          dependencyCheck=None,
                                          outputCB=outputCB,
                                          updateCB=updateCB,
                                          )
    if removeStale:
        for candidateRelativePath, _ in utils.walkfiles(destinationDir):
            candidateFullPath = join(destinationDir, candidateRelativePath)
            if candidateFullPath not in outputFiles:
                unlink(candidateFullPath)
