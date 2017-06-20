# encoding=utf-8
"""Deploy third-party files"""
import json
from os import listdir
from os.path import (join,
                     isdir,
                     splitext,
                     )
from shutil import rmtree
from subprocess import Popen
from wdeploy import (task,
                     utils,
                     )
from wdeploy.dependencies import extensionCheck
from wdeploy.user import (as_user,
                          original_user,
                          original_group,
                          writeDestinationFile,
                          readSourceFile,
                          )
from .css import cssProcess
from .js import jsProcess
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


@task(sourcePathArguments=['listDir'],
      destinationPathArguments=['jsDir', 'cssDir'])
def third(listDir,
          jsDir,
          cssDir,
          ):
    """Read third-party dependencies descriptions and deploy them

    Parameters
    ----------
    listDir : string
        The path to a directory containing the third party config files.
        Relative to ROOT.
    jsDir : string
        The output directory for Javascript files. Relative to PREFIX.
    cssDir : string
        The output directory for CSS files. Relative to PREFIX.


    Notes
    -----
    Config files are JSON files that must represent a dictionary.
    Possible properties are:
    - source: the source of the third party files. Have a mandatory property
      named "type".
    - prefix: the prefix for output directories
    - files: list of files to process

    For "git" source type, the source object can have:
    - url: the repository URL
    - tag: the tag to checkout

    File list can have the following properties:
    - "js": a dictionary whose key are source files and values are destination
      name.

    In all cases, destination names will be prefixed with "prefix" and put in
    appropriate directories (<js path>/<prefix>/file.js)
    """
    for fileName in listdir(listDir):
        filePath = join(listDir,
                        fileName)
        name = splitext(fileName)[0]
        with open(filePath, 'r') as inFile:
            cfg = json.load(inFile)
            thirdPath = prepareFiles(name,
                                     cfg['source'])
            try:
                prefix = cfg['prefix']
            except KeyError:
                prefix = name
            deployThird(thirdPath,
                        prefix,
                        cfg['files'],
                        jsDir,
                        cssDir,
                        )


def _outputPathHandlerFactory(outputDir,
                              prefix,
                              fileslist):
    """Create an outputCB handler for checkDependencies().

    Parameters
    ----------
    outputDir : string
        Base output directory
    prefix : string
        Module specific prefix, appended to outputDir
    fileslist : dictionary
        Key=source relative path, Value=destination relative directory

    Returns
    -------
    runnable
        A runnable suitable to be used as the outputCB argument of
        checkDependencies().
    """
    def runnable(relativePath):
        return join(outputDir,
                    prefix,
                    fileslist[relativePath],
                    )
    return runnable


def deployThird(sourceDir,
                prefix,
                files,
                jsDir,
                cssDir):
    """Copy files from third party source to deployment directory.

    Parameters
    ----------
    sourceDir : string
        The source path where are stored the files for the dependency
    prefix : string
        The dependency's prefix name
    files : dict
        A dictionary where values are a list of filenames, and keys can be 'js'
        and 'css'
    jsDir : string
        The base Javscript directory. Javascript files will be copied there
        under the prefix directory.
    cssDir : string
        The base CSS directory. CSS files will be copied there under the prefix
        directory.
    """
    if 'js' in files:
        utils.checkDependencies(baseDir=sourceDir,
                                includeDirs=None,
                                localInclude=False,
                                validityCheck=extensionCheck('js'),
                                dependencyCheck=None,
                                outputCB=_outputPathHandlerFactory(jsDir,
                                                                   prefix,
                                                                   files['js']),
                                updateCB=updateJSFile,
                                filesList=files['js'],
                                )
    if 'css' in files:
        utils.checkDependencies(baseDir=sourceDir,
                                includeDirs=None,
                                localInclude=False,
                                validityCheck=extensionCheck('css'),
                                dependencyCheck=None,
                                outputCB=_outputPathHandlerFactory(cssDir,
                                                                   prefix,
                                                                   files['css'],
                                                                   ),
                                updateCB=updateCSSFile,
                                filesList=files['css'],
                                )
    if 'cssother' in files:
        lsof = files['cssother']
        utils.checkDependencies(baseDir=sourceDir,
                                includeDirs=None,
                                localInclude=False,
                                validityCheck=None,
                                dependencyCheck=None,
                                outputCB=_outputPathHandlerFactory(cssDir,
                                                                   prefix,
                                                                   lsof),
                                updateCB=copyFile,
                                filesList=lsof)


def copyFile(sourcepath,
             destinationpath):
    writeDestinationFile(destinationpath,
                         readSourceFile(sourcepath))


def updateJSFile(sourcePath,
                 destPath,
                 ):
    """Process a JS file using uglifyjs."""
    jsProcess(sourcePath, destPath)


def updateCSSFile(sourcePath,
                  destPath,
                  ):
    """Minify a CSS file."""
    cssProcess(sourcePath, destPath)


@as_user(original_user, original_group)
def prepareFiles(name,
                 source,
                 ):
    """Prepare files according to the settings in source.

    source if taken from a config file.
    This function return a path containing the prepared files. If it fails, an
    exception is raised.
    """
    if source['type'] == 'git':
        return prepareGIT(name,
                          source)
    raise NotImplementedError('Unsupported source type: %s' % source['type'])


def prepareGIT(name,
               source,
               ):
    """Prepare files from a GIT repository."""
    infoFile = join(utils.dataPath(),
                    '%s.third' % name)
    try:
        with open(infoFile, 'r') as inFile:
            installedString = inFile.read()
    except OSError:
        installedString = ''

    if 'tag' not in source:
        tagName = ''
    else:
        tagName = source['tag']
    expectedInstallString = '%s:%s' % (source['url'], tagName)
    thirdPathName = '%s.files' % name
    thirdPath = join(utils.dataPath(),
                     thirdPathName)
    if expectedInstallString == installedString:
        return thirdPath

    if isdir(thirdPath):
        rmtree(thirdPath)

    gitPath = utils.which(utils.GIT)
    cloneProcessArgs = [gitPath,
                        'clone',
                        source['url'],
                        thirdPathName,
                        ]
    cloneProcess = Popen(cloneProcessArgs,
                         cwd=utils.dataPath())
    cloneResult = cloneProcess.wait()
    if cloneResult != 0:
        raise Exception('Error when cloning repository for %s' % name)

    if tagName:
        checkoutProcessArgs = [gitPath,
                               'checkout',
                               'tags/%s' % source['tag']]
    else:
        checkoutProcessArgs = [gitPath,
                               'checkout',
                               'master']
    checkoutProcess = Popen(checkoutProcessArgs,
                            cwd=thirdPath)
    checkoutResult = checkoutProcess.wait()
    if checkoutResult != 0:
        raise Exception('Error when checking out tag %s for %s' %
                        (tagName,
                         name))

    with open(infoFile, 'w') as outFile:
        outFile.write(expectedInstallString)

    return thirdPath
