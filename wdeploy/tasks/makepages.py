# encoding=utf-8
"""Generate static pages."""
from os.path import (getmtime,
                     join,
                     )
from wdeploy import (task,
                     utils,
                     )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


@task(sourcePathArguments=['sourceDir'],
      destinationPathArguments=['targetDir'],
      )
def makepages(sourceDir,
              targetDir,
              headerNames,
              footerNames,
              pagesList):
    """Create files by merging headers, body and footers.

    Parameters
    ----------
    sourceDir : string
        The path to all the files to merge together. Relative to ROOT
    targetDir : string
        The path to put created files into. Relative to PREFIX
    headerNames : list(string)
        List of headers to prepend to bodies (in order). The names listed here
        will get the '.html' suffix appended to them, and the script will look
        for them in sourceDir.
    footerNames : list(string)
        List of footers. Same rules as headerNames.
    pagesList : list(tuple(string,string)
        List of pages to generate. The tuples contain the title of the page, and
        the name of the file to use as the body. Same rules applies as for
        headerNames.


    Notes
    -----
    The title will be used anywhere the '%TITLE%' string is used (header, body,
    footer).
    """
    header = u''
    decoratorTime = 0
    if headerNames:
        logg.info('Reading headers for file merging')
        for headerName in headerNames:
            logg.debug('Reading header: %s' % headerName)
            headerPath = join(sourceDir, '%s.html' % headerName)
            thisHeaderTime = getmtime(headerPath)
            if thisHeaderTime > decoratorTime:
                decoratorTime = thisHeaderTime
            with utils.open_utf8(headerPath, 'r') as inFile:
                header += inFile.read()
    footer = u''
    if footerNames:
        logg.info('Reading footers for file merging')
        for footerName in footerNames:
            logg.debug('Reading footer: %s' % footerName)
            footerPath = join(sourceDir, '%s.html' % footerName)
            thisFooterTime = getmtime(footerPath)
            if thisFooterTime > decoratorTime:
                decoratorTime = thisFooterTime
            with utils.open_utf8(footerPath, 'r') as inFile:
                footer += inFile.read()

    logg.info('Generating merged files')
    for title, bodyFile in pagesList:
        logg.debug('Merging file %s' % bodyFile)
        sourcePath = join(sourceDir, '%s.html' % bodyFile)
        targetPath = join(targetDir, '%s.html' % bodyFile)

        sourceTime = min(getmtime(sourcePath),
                         decoratorTime,
                         )
        try:
            targetTime = getmtime(targetPath)
        except OSError:
            targetTime = 0

        if sourceTime <= targetTime:
            continue

        with utils.open_utf8(targetPath, 'w') as outFile,\
                utils.open_utf8(sourcePath, 'r') as inFile:
            content = u'%s%s%s' % (header, inFile.read(), footer)
            content = content.replace(u'%TITLE%', title)
            outFile.write(content)
