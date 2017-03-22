# encoding=utf-8
"""
Read project configuration
"""
import sys
from os import (
        environ,
)

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


def config(configPath=None):
    """Return the project configuration.

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
        pass
    sys.dont_write_bytecode = True
    if configPath:
        searchPath = configPath
    elif 'DEPLOY_CONFIG' in environ:
        searchPath = environ['DEPLOY_CONFIG']
    else:
        searchPath = None
    if searchPath:
        sys.path.insert(0, searchPath)
    import config as projectConfig
    sys.dont_write_bytecode = False
    if searchPath:
        sys.path.remove(searchPath)
    configFunction.cache = projectConfig
    return projectConfig
