# encoding=utf-8
"""
Create WSGI CGI scripts for Django applications.
"""
from os.path import (
        dirname,
        join,
        )

from wdeploy import (
        task,
        utils,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task(destinationPathArguments=['path'])
def cgi(path):
    """Create a wsgi CGI script in the given path.

    This is a django script only. No customisation needed.
    """
    directoryPath = dirname(path)
    utils.real_mkdir(directoryPath)
    with utils.open_utf8(path, 'w') as outFile:
        outFile.write("""import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
""")
    utils.cfg_chown(path)
    utils.cfg_chmod(path)
