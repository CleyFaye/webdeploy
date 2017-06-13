# encoding=utf-8
from os.path import (join,
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
                          crawlDestination,
                          )
from wdeploy.dependencies import extensionCheck

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


def _jsProcess(sourceFile):
    """Return a JS minifier process returning the minified output as stdout"""
    if utils.isToolPresent('closure-compiler.sh'):
        args = []
        return utils.pipeRun('closure-compiler.sh', sourceFile, args)
    if utils.isToolPresent('uglifyjs'):
        args = ['-c',
                '-m',
                ]
        return utils.pipeRun('uglifyjs', sourceFile, args)
    if utils.isToolPresent('yui-compressor'):
        args = ['--type',
                'js',
                '--charset',
                'utf-8',
                ]
        return utils.pipeRun('yui-compressor', sourceFile, args)
    raise RuntimeError('No JS minification facilities present!'
                       + '(tried closure-compiler.sh, uglifyjs, '
                       + 'yui-compressor)')


@as_user(original_user, original_group)
def _jsProcessFromSource(source):
    """Read and process a source css file

    Returns
    -------
    string
        The processed file content
    """
    with utils.open_utf8(source, 'r') as inFile:
        jsProc = _jsProcess(inFile)
        result = jsProc.stdout.read()
        jsProc.wait()
        if jsProc.returncode != 0:
            raise RuntimeError('Error when minifying Javascript %s' % source)
        return result


def jsProcess(source, dest):
    """Process a css file into a minified css file"""
    writeDestinationFile(dest,
                         _jsProcessFromSource(source),
                         )


@task(sourcePathArguments=['sourceDir', 'includeDirs'],
      destinationPathArguments=['destinationDir'],
      )
def js(sourceDir,
       destinationDir,
       removeStale=True):
    """Process all Javascript files drom sourceDir.

    This task will look for changes in the source directory, and process/copy
    files in the destination directory.

    Javscript files will be minified.
    """
    def outputCB(relativePath):
        return join(destinationDir, relativePath)

    def updateCB(absoluteSource, absoluteDest):
        jsProcess(absoluteSource,
                  absoluteDest,
                  )

    outputFiles = utils.checkDependencies(baseDir=sourceDir,
                                          includeDirs=None,
                                          localInclude=True,
                                          validityCheck=extensionCheck(['js']),
                                          dependencyCheck=None,
                                          outputCB=outputCB,
                                          updateCB=updateCB,
                                          )
    if removeStale:
        for candidateRelativePath, name in crawlDestination(destinationDir):
            candidateFullPath = join(destinationDir,
                                     candidateRelativePath,
                                     name)
            if candidateFullPath not in outputFiles:
                unlink(candidateFullPath)
