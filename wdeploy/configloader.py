# encoding=utf-8
"""Read project configuration"""
import sys
from os import environ
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


def config(configPath=None):
    """Return the project configuration.

    Notes
    -----

    The project configuration is a python file named config.py containing
    specific variables. We look in three places for this file:
    - If configPath is provided, it is used as the path to the config.py file
    - If an environment variable named DEPLOY_CONFIG exist, it is used as a
      path containing the config.py file
    - Otherwise, the current directory is used.
    """
    configFunction = config
    try:
        return configFunction.cache
    except AttributeError:
        logg.debug('First call to config(), no cache available')

    oldBytecodeDisabledStatus = sys.dont_write_bytecode
    if oldBytecodeDisabledStatus is False:
        logg.debug('Disabling bytecode generation')
        sys.dont_write_bytecode = True

    if configPath:
        searchPath = configPath
        logg.info('Using config path %s' % searchPath)
    elif 'DEPLOY_CONFIG' in environ:
        searchPath = environ['DEPLOY_CONFIG']
        logg.info('Using config env. variable %s' % searchPath)
    else:
        searchPath = None
        logg.info('No config path provided')
    if searchPath:
        sys.path.insert(0, searchPath)
    import config as projectConfig
    if searchPath:
        sys.path.remove(searchPath)

    if oldBytecodeDisabledStatus is False:
        logg.debug('Enabling bytecode generation')
        sys.dont_write_bytecode = False

    logg.debug('Caching configuration')
    configFunction.cache = projectConfig
    return projectConfig
