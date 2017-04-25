# encoding=utf-8
"""
Generate static pages.
"""
from os.path import (
        getmtime,
        join,
        )
from wdeploy import (
        task,
        utils,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task(sourcePathArguments=['sourceDir'],
      destinationPathArguments=['targetDir'],
      )
def makepages(sourceDir, targetDir, headerNames, footerNames, pagesList):
    """Create static page files by merging header, body and footer.

    headerNames and footerNames are array of filename in sourceDir.
    They are added in order to each final pages.
    pagesList is a list of tuples containing the page title and the page body
    file, relative to sourceDir.

    The file suffix .html will be appended to file names.

    The title will be used anywhere the '%TITLE%' string is used (header, body,
    footer).
    """
    header = u''
    headerTime = 0
    if headerNames:
        for headerName in headerNames:
            headerPath = join(sourceDir, '%s.html' % headerName)
            thisHeaderTime = getmtime(headerPath)
            if thisHeaderTime > headerTime:
                headerTime = thisHeaderTime
            with utils.open_utf8(headerPath, 'r') as inFile:
                header += inFile.read()
    footer = u''
    footerTime = 0
    if footerNames:
        for footerName in footerNames:
            footerPath = join(sourceDir, '%s.html' % footerName)
            thisFooterTime = getmtime(footerPath)
            if thisFooterTime > footerTime:
                footerTime = thisFooterTime
            with utils.open_utf8(footerPath, 'r') as inFile:
                footer += inFile.read()

    if headerTime > footerTime:
        decoratorTime = headerTime
    else:
        decoratorTime = footerTime

    for page in pagesList:
        sourcePath = join(sourceDir, '%s.html' % page[1])
        targetPath = join(targetDir, '%s.html' % page[1])

        sourceTime = getmtime(sourcePath)
        try:
            targetTime = getmtime(targetPath)
        except OSError:
            targetTime = 0

        if sourceTime <= targetTime and decoratorTime <= targetTime:
            continue

        with utils.open_utf8(targetPath, 'w') as outFile,\
                utils.open_utf8(sourcePath, 'r') as inFile:
            content = u'%s%s%s' % (header, inFile.read(), footer)
            content = content.replace(u'%TITLE%', page[0])
            outFile.write(content)
