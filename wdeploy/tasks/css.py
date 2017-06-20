# encoding=utf-8
import re
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
                          crawlDestination,
                          )
from wdeploy.dependencies import extensionCheck

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')

LESS_IMPORT_RE = re.compile(r'@import(?: +)\"(?P<import>.+)\";')


def _lessProcess(sourceFile, includeDirs):
    """Return a lessc process taking sourceFile as stdin"""
    args = []
    if includeDirs:
        for includeDir in includeDirs:
            args += ['--include-path=%s' % includeDir]
    args += ['-sm=on',
             '-ru',
             '-x',
             '-']
    return utils.pipeRun('lessc', sourceFile, args)


def _cssProcess(sourceFile):
    """Return a css minifier process taking sourceFile as stdin"""
    if utils.isToolPresent('yui-compressor'):
        args = ['--type',
                'css',
                '--charset',
                'utf-8',
                ]
        return utils.pipeRun('yui-compressor', sourceFile, args)
    if utils.isToolPresent('cleancss'):
        args = ['-e',
                '--s1',
                '-s',
                ]
        return utils.pipeRun('cleancss', sourceFile, args)
    if utils.isToolPresent('cssmin'):
        return utils.pipeRun('cssmin', sourceFile, [])
    raise RuntimeError('No CSS minification facilities present!'
                       + '(tried yui-compressor, cleancss, cssmin)')


@as_user(original_user, original_group)
def _lessProcessFromSource(source, includeDirs):
    """Read and process a source less file

    Returns
    -------
    string
        The processed file content
    """
    with utils.open_utf8(source, 'r') as inFile:
        lessProc = _lessProcess(inFile, includeDirs)
        cssProc = _cssProcess(lessProc.stdout)
        result = cssProc.stdout.read()
        cssProc.wait()
        lessProc.wait()
        if cssProc.returncode != 0 or lessProc.returncode != 0:
            raise RuntimeError('Error while processing less file: %s' % source)
        return result


@as_user(original_user, original_group)
def _cssProcessFromSource(source):
    """Read and process a source css file

    Returns
    -------
    string
        The processed file content
    """
    with utils.open_utf8(source, 'r') as inFile:
        cssProc = _cssProcess(inFile)
        result = cssProc.stdout.read()
        cssProc.wait()
        if cssProc.returncode != 0:
            raise RuntimeError('Error while processing CSS file %s' % source)
        return result


def lessProcess(source, dest, includeDirs):
    """Process a less file into a css file"""
    writeDestinationFile(dest,
                         _lessProcessFromSource(source, includeDirs),
                         )


def cssProcess(source, dest):
    """Process a css file into a minified css file"""
    writeDestinationFile(dest,
                         _cssProcessFromSource(source),
                         )


@task(sourcePathArguments=['sourceDir', 'includeDirs'],
      destinationPathArguments=['destinationDir'],
      )
def css(sourceDir,
        destinationDir,
        includeDirs=None,
        removeStale=True):
    """Process all css/less files from sourceDir.

    This task will look for changes in the source directory, and process/copy
    files in the destination directory.

    CSS files will be minified.
    LESSC files (.less) will be parsed for includes, then processed using lessc
    to produce an output file with the same basename and the .css suffix, then
    minified.

    includeDirs is a list of directories included when parsing import
    directives in lessc files.
    """
    def dependencyCheck(absolutePath):
        with utils.open_utf8(absolutePath, 'r') as src:
            imports = [x.group('import')
                       for x in LESS_IMPORT_RE.finditer(src.read())
                       ]
        fixedimports = []
        for importname in imports:
            if importname.endswith('.less'):
                fixedimports.append(importname)
            else:
                fixedimports.append('%s.less' % importname)
        return fixedimports

    def outputCB(relativePath):
        name, _ = splitext(relativePath)
        return join(destinationDir, '%s.css' % name)

    def updateCB(absoluteSource, absoluteDest):
        _, ext = splitext(absoluteSource)
        if ext == '.less':
            lessProcess(absoluteSource,
                        absoluteDest,
                        includeDirs,
                        )
        else:
            cssProcess(absoluteSource, absoluteDest)

    outputFiles = utils.checkDependencies(baseDir=sourceDir,
                                          includeDirs=includeDirs,
                                          localInclude=True,
                                          validityCheck=extensionCheck([
                                              'css',
                                              'less',
                                          ]),
                                          dependencyCheck=dependencyCheck,
                                          outputCB=outputCB,
                                          updateCB=updateCB,
                                          )
    if removeStale:
        for candidateRelativePath, name in crawlDestination(destinationDir):
            candidateFullPath = join(destinationDir,
                                     candidateRelativePath,
                                     name,
                                     )
            if candidateFullPath not in outputFiles:
                unlink(candidateFullPath)
