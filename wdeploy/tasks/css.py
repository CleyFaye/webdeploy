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

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')

LESS_IMPORT_RE = re.compile(r'@import(?: +)\"(?P<import>.+)\";')


def _lessProcess(sourceFile, includeDirs):
    """Return a lessc process taking sourceFile as stdin"""
    args = []
    if includeDirs:
        for includeDir in includeDirs:
            args += ['--include-path=%s' % includeDir]
    args += ['-sm', 'on',
             '-ru',
             '-x',
             '-']
    return utils.pipeRun('lessc', sourceFile, args)


def _cssProcess(sourceFile):
    """Return a css minifier process taking sourceFile as stdin"""
    if utils.isToolPresent('cleancss'):
        args = ['-e',
                '--s1',
                '-s',
                ]
        return utils.pipeRun('cleancss', sourceFile, args)
    if utils.isToolPresent('cssmin'):
        return utils.pipeRun('cssmin', sourceFile, [])


def lessProcess(source, dest, includeDirs):
    """Process a less file into a css file"""
    with utils.open_utf8(source, 'r') as inFile:
        lessProc = _lessProcess(inFile, includeDirs)
        cssProc = _cssProcess(lessProc.stdout)
        with utils.open_utf8(dest, 'w') as outFile:
            outFile.write(cssProc.read())


def cssProcess(source, dest):
    """Process a css file into a minified css file"""
    with utils.open_utf8(source, 'r') as inFile:
        cssProc = _cssProcess(inFile)
        with utils.open_utf8(dest, 'w') as outFile:
            outFile.write(cssProc.read())


@task(sourcePathArguments=['sourceDir', 'includeDirs'],
      destinationPathArguments=['destinationDir'],
      )
def css(sourceDir,
        destinationDir,
        includeDirs=None,
        removeStale=True):
    """Process all css/less files drom sourceDir.

    This task will look for changes in the source directory, and process/copy
    files in the destination directory.

    CSS files will be minified.
    LESSC files (.less) will be parsed for includes, then processed using lessc
    to produce an output file with the same basename and the .css suffix, then
    minified.

    includeDirs is a list of directories included when parsing import
    directives in lessc files.
    """

    def validityCheck(absolutePath):
        _, ext = splitext(absolutePath)
        return ext in ['.css', '.less']

    def dependencyCheck(absolutePath):
        with utils.open_utf8(absolutePath, 'r') as src:
            imports = [x.group('import')
                       for x in LESS_IMPORT_RE.finditer(src.read())
                       ]
        return imports

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

    outputFiles = utils.checkDependencies(sourceDir,
                                          includeDirs,
                                          validityCheck,
                                          dependencyCheck,
                                          outputCB,
                                          updateCB,
                                          )
    if removeStale:
        for candidateRelativePath, _ in utils.walkfiles(destinationDir):
            candidateFullPath = join(destinationDir, candidateRelativePath)
            if candidateFullPath not in outputFiles:
                unlink(candidateFullPath)
