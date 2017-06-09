# encoding=utf-8
"""Create WSGI CGI scripts for Django applications."""
from os.path import isfile
from wdeploy import (task,
                     utils,
                     )
from wdeploy.user import (as_user,
                          prefix_user,
                          prefix_group,
                          )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


SCRIPT_BASE = """import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()"""


@task(destinationPathArguments=['path'])
@as_user(userName=prefix_user,
         groupName=prefix_group,
         )
def cgi(path):
    """Create a wsgi CGI script in the given path.

    Notes
    -----
    This is a django script only. No customisation needed.
    If the file already exist, it is not replaced or erased.
    """
    if isfile(path):
        logg.info('WSGI script already exists; not overwriting')
        return
    logg.info('Creating WSGI script in "%s"' % path)
    utils.makeParentPath(path)
    with utils.open_utf8(path, 'w') as outFile:
        outFile.write(SCRIPT_BASE)
