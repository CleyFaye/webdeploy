# encoding=utf-8
"""
Generate Apache configuration for Django application.
"""
from os.path import (
        dirname,
        join,
        )

from wdeploy import (
        config,
        runTask,
        task,
        utils,
        )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


@task()
def apachecfg(name, apacheConfig):
    """Prepare the application to run on an apache2 server.

    This will produce the apache site configuration for the given host and
    generate the appropriate CGI file.

    name is the name of the generated configuration file.

    apacheConfig is a dictionary that can contain:
    - alias: an array of tuple for aliasing URL to directories on the FS
    - cgi: a list of path to append to the python execution path
    - loglevel: the apache log level for this virtual host. If not provided,
                default to 'info'.
    - hostname: the name of this vhost.
    - tls: a tuple containing path to the private and public key. If not
           provided, only HTTP configuration is produced.
           An optional third value can be used to indicate the CA certificate
           file path.
           Note that these path are not taken relative to the PREFIX, since
           keys must NOT be present there.

    Note that the configuration file will be created in PREFIX; a symlink to it
    in the appropriate apache configuration directory is a good idea.
    """
    cgiName = 'cgi/wsgi.py'
    runTask(('Create WSGI script', 'cgi', cgiName))
    fullCGIPath = join(config().PREFIX, cgiName)
    apacheFullPath = join(config().PREFIX, name)
    apacheFullDir = dirname(apacheFullPath)
    utils.real_mkdir(apacheFullDir)

    if 'hostname' in apacheConfig and apacheConfig['hostname']:
        hostName = apacheConfig['hostname']
    else:
        hostName = 'localhost'

    pythonPath = ':'.join([join(config().PREFIX, a).replace(' ', '\\ ')
                           for a in apacheConfig['cgi']])

    if 'loglevel' in apacheConfig and apacheConfig['loglevel']:
        logLevel = apacheConfig['loglevel']
    else:
        logLevel = 'info'

    with utils.open_utf8(apacheFullPath, 'w') as outFile:
        if 'tls' in apacheConfig and apacheConfig['tls']:
            configWithTLS = [False, True]
        else:
            configWithTLS = [False]
        for useTLS in configWithTLS:
            # VHost header
            if useTLS:
                outFile.write('<VirtualHost *:443>\n')
                processGroupSuffix = '_tls'
            else:
                outFile.write('<VirtualHost *:80>\n')
                processGroupSuffix = ''
            outFile.write('ServerName "%s"\n' % hostName)
            # Log Level
            outFile.write('LogLevel %s\n' % logLevel)
            # WSGI Script
            outFile.write('WSGIDaemonProcess %s%s python-path=%s\n' %
                          (config().PROJECT_NAME,
                           processGroupSuffix,
                           pythonPath,
                           ),
                          )
            outFile.write('WSGIProcessGroup %s%s\n' %
                          (config().PROJECT_NAME,
                           processGroupSuffix,
                           ),
                          )
            outFile.write('WSGIScriptAlias / %s\n' % fullCGIPath)
            apacheGrantAccess(outFile, 'cgi')
            # Aliases
            if 'alias' in apacheConfig and apacheConfig['alias']:
                for alias in apacheConfig['alias']:
                    outFile.write('Alias /%s/ %s/\n' %
                                  (alias[0], join(config().PREFIX, alias[1])))
                    apacheGrantAccess(outFile, alias[1])
            # TLS
            if useTLS:
                outFile.write('SSLEngine On\n')
                outFile.write('SSLCertificateFile %s\n' %
                              apacheConfig['tls'][1])
                outFile.write('SSLCertificateKeyFile %s\n' %
                              apacheConfig['tls'][0])
                if len(apacheConfig['tls']) == 3:
                    outFile.write('SSLCACertificateFile %s\n' %
                                  apacheConfig['tls'][2])
                outFile.write('SSLVerifyClient None\n')
            # VHost footer
            outFile.write('</VirtualHost>\n')
    utils.cfg_chown(apacheFullPath)
    utils.cfg_chmod(apacheFullPath)


def apacheGrantAccess(outFile, directory):
    """Write an all-access directive to a directory in an apache config dir."""
    outFile.write('<Directory %s>\n' % join(config().PREFIX, directory))
    outFile.write('Require all granted\n')
    outFile.write('</Directory>\n')
