# encoding=utf-8
"""
Enable/disable Apache site config.
"""
from subprocess import (
        call,
        )

from wdeploy import (
        task,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task
def a2site(enable, siteName):
    """Enable or disable an apache2 site configuration.

    This rely on a2ensite and a2dissite. See their respective man pages for
    more info.
    """
    if enable:
        callArgs = ['a2ensite']
    else:
        callArgs = ['a2dissite']
    callArgs += [siteName]
    retVal = call(callArgs)
    if retVal == 0:
        return
    raise Exception('Error when enabling/disabling site "%s"' % siteName)
