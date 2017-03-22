# encoding=utf-8
"""
Deploy third-party files
"""
import json
from os import (
        listdir,
        )
from os.path import (
        dirname,
        getmtime,
        join,
        isdir,
        splitext,
        )
from shutil import (
        rmtree,
        )
from subprocess import Popen

from wdeploy import (
        config,
        task,
        utils,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task
def third(listDir, jsDir, cssDir):
    """Read third-party dependencies descriptions and deploy the appropriate
    files.

    Arguments must be:
    - Directory containing config files. Relative to ROOT.
    - Output directory for JavaScript files. Relative to PREFIX.
    - Output directory for CSS files. Relative to PREFIX.

    Config files are JSON strings that must represent a dictionary.
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
    # TODO: add support for CSS.
    listDir = join(config().ROOT, listDir)
    for fileName in listdir(listDir):
        filePath = join(listDir, fileName)
        name = splitext(fileName)[0]
        with open(filePath, 'r') as inFile:
            cfg = json.load(inFile)
            thirdPath = prepareFiles(name, cfg['source'])
            try:
                prefix = cfg['prefix']
            except:
                prefix = name
            deployThird(
                    name,
                    thirdPath,
                    prefix,
                    cfg['files'],
                    join(config().PREFIX, jsDir),
                    join(config().PREFIX, cssDir),
                    )


def deployThird(name,
                sourceDir,
                prefix,
                files,
                jsDir,
                cssDir):
    """Copy files from third party source to deployment directory."""
    if 'js' in files:
        handleFiles(sourceDir, jsDir, prefix, files['js'], uglifyJS)


def handleFiles(sourceDir, destDir, prefix, files, handler):
    """Process list of files.

    Will only update newer files, and chmod/chown them accordinyl.
    """
    for fileName in files:
        destName = files[fileName]
        destPath = join(destDir, prefix, destName)
        srcPath = join(sourceDir, fileName)
        sourceTime = getmtime(srcPath)
        try:
            destTime = getmtime(destPath)
        except:
            destTime = sourceTime - 1
        if sourceTime <= destTime:
            continue
        parentDir = dirname(destPath)
        utils.real_mkdir(parentDir)
        handler(srcPath, destPath)
        utils.cfg_chown(destPath)
        utils.cfg_chmod(destPath)


def uglifyJS(sourcePath, destPath):
    """Uglify a JS file using uglifyjs."""
    uglifyJsPath = utils.which('uglifyjs')
    args = [uglifyJsPath, '-o', destPath, '-c', '--', sourcePath]
    process = Popen(args)
    result = process.wait()
    if result != 0:
        raise Exception('Error when minifying %s' % sourcePath)


def prepareFiles(name, source):
    """Prepare files according to the settings in source.

    source if taken from a config file.
    This function return a path containing the prepared files. If it fails, an
    exception is raised.
    """
    if source['type'] == 'git':
        return prepareGIT(name, source)
    raise NotImplementedError('Unsupported source type: %s' % source['type'])


def prepareGIT(name, source):
    """Prepare files from a GIT repository."""
    infoFile = join(utils.dataPath(), '%s.third' % name)
    try:
        with open(infoFile, 'r') as inFile:
            installedString = inFile.read()
    except:
        installedString = ''

    if 'tag' not in source:
        tagName = ''
    else:
        tagName = source['tag']
    expectedInstallString = '%s:%s' % (source['url'], tagName)
    thirdPathName = '%s.files' % name
    thirdPath = join(utils.dataPath(), thirdPathName)
    if expectedInstallString == installedString:
        return thirdPath

    if isdir(thirdPath):
        rmtree(thirdPath)

    gitPath = utils.which(utils.GIT)
    cloneProcessArgs = [gitPath, 'clone', source['url'], thirdPathName]
    cloneProcess = Popen(cloneProcessArgs, cwd=utils.dataPath())
    cloneResult = cloneProcess.wait()
    if cloneResult != 0:
        raise Exception('Error when cloning repository for %s' % name)

    if tagName:
        checkoutProcessArgs = [gitPath, 'checkout', 'tags/%s' % source['tag']]
    else:
        checkoutProcessArgs = [gitPath, 'checkout', 'master']
    checkoutProcess = Popen(checkoutProcessArgs, cwd=thirdPath)
    checkoutResult = checkoutProcess.wait()
    if checkoutResult != 0:
        raise Exception('Error when checking out tag %s for %s' %
                        (tagName, name))

    with open(infoFile, 'w') as outFile:
        outFile.write(expectedInstallString)

    return thirdPath
