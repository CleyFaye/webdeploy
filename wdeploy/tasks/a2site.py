# encoding=utf-8
"""Enable/disable Apache site config."""
from subprocess import call
from wdeploy import task
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


@task()
def a2site(enable, siteName):
    """Enable or disable an apache2 site configuration.

    Parameters
    ----------
    enable : bool
        Indicate if siteName must be enabled or disabled
    siteName : string
        The name of a config file in the apache sites-available directory


    Notes
    -----
    This rely on a2ensite and a2dissite. See their respective man pages for
    more info.
    """
    if enable:
        callArgs = ['a2ensite']
        logg.info('Enabling apache site %s' % siteName)
    else:
        callArgs = ['a2dissite']
        logg.info('Disabling apache site %s' % siteName)
    callArgs += [siteName]
    retVal = call(callArgs)
    if retVal == 0:
        return
    raise Exception('Error when enabling/disabling site "%s"' % siteName)
