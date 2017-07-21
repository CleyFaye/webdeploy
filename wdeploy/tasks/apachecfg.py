# encoding=utf-8
"""Generate Apache configuration for Django application."""
from os.path import (dirname,
                     join,
                     )

from wdeploy import (config,
                     runTask,
                     task,
                     utils,
                     )
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


# List of mimetypes to pass through DEFLATE
MIME_COMPRESS = ['text/plain',
                 'text/xml',
                 'text/html',
                 'text/css',
                 'text/csv',
                 'application/javascript',
                 'application/xml',
                 'image/svg+xml',
                 'image/svg']


def _writeRedirect(outFile,
                   hostName,
                   ):
    """Write a redirect from HTTP to HTTPS"""
    outFile.write("""<VirtualHost *:80>
                  ServerName %s
                  <IfModule mod_rewrite.c>
                  RewriteEngine On
                  RewriteCond %%{HTTPS} off
                  RewriteRule (.*) https://%%{HTTP_HOST}%%{REQUEST_URI}
                  </IfModule>
                  <IfModule !mod_rewrite.c>
                  Redirect permanent / https://%s/
                  </IfModule>
                  </VirtualHost>\n""" % (hostName, hostName))


def _writeVHost(outFile,
                fullCGIPath,
                apache_config,
                ):
    """Write a vhost entry."""
    # VHost header
    if apache_config['tls']:
        _writeRedirect(outFile,
                       apache_config['hostname'],
                       )
        outFile.write('<VirtualHost *:443>\n')
    else:
        outFile.write('<VirtualHost *:80>\n')
    outFile.write('ServerName "%s"\n' % apache_config['hostname'])
    # Log Level
    outFile.write('LogLevel %s\n' % apache_config['loglevel'])
    # WSGI Script
    pythonPath = join(config().PREFIX,
                      apache_config['venv'],
                      )
    appPath = join(config().PREFIX,
                   apache_config['app'],
                   )
    outFile.write('WSGIDaemonProcess %s python-home=%s python-path=%s\n' %
                  (config().PROJECT_NAME,
                   pythonPath,
                   appPath,
                   ),
                  )
    outFile.write('WSGIProcessGroup %s\n' %
                  (config().PROJECT_NAME,
                   ),
                  )
    outFile.write('WSGIScriptAlias / %s process-group=%s\n'
                  % (fullCGIPath,
                     config().PROJECT_NAME,
                     ),
                  )
    apacheGrantAccess(outFile, 'cgi')
    # Aliases
    for alias in apache_config['alias']:
        if len(alias) >= 3:
            cacheStrategy = alias[2]
        else:
            cacheStrategy = None
        outFile.write('Alias /%s/ %s/\n' %
                      (alias[0], join(config().PREFIX, alias[1])))
        apacheGrantAccess(outFile, alias[1], cacheStrategy)
    # Compression
    if apache_config['enable_compression']:
        outFile.write('<IfModule mod_deflate.c>\n')
        outFile.write('SetOutputFilter DEFLATE\n')
        outFile.write('DeflateCompressionLevel 9\n')
        for mime_format in MIME_COMPRESS:
            outFile.write('AddOutputFilterByType DEFLATE %s\n' % mime_format)
        outFile.write('Header append Vary User-Agent env=!dont-vary\n')
        outFile.write('</IfModule>\n')
        pass
    # TLS
    if apache_config['tls']:
        outFile.write('SSLEngine On\n')
        outFile.write('SSLCertificateFile %s\n' %
                      apache_config['tls'][1])
        outFile.write('SSLCertificateKeyFile %s\n' %
                      apache_config['tls'][0])
        if len(apache_config['tls']) == 3:
            outFile.write('SSLCACertificateFile %s\n' %
                          apache_config['tls'][2])
        outFile.write('SSLVerifyClient None\n')
        outFile.write('Header always set Strict-Transport-Security '
                      + '"max-age=63072001; includeSubdomains;"\n')
    # VHost footer
    outFile.write('</VirtualHost>\n')


@task()
def apachecfg(name, apacheConfig):
    """Prepare the application to run on an apache2 server.

    This will produce the apache site configuration for the given host and
    generate the appropriate CGI file.

    name is the name of the generated configuration file.

    apacheConfig is a dictionary that can contain:
    - alias: an array of tuple for aliasing URL to directories on the FS. Tuple
             can either have two values (URL, directory) or three values
             (URL, directory, cache strategy).
    - venv: the path to the VENV (relative to PREFIX)
    - app: the path to the app (relative to PREFIX)
    - loglevel: the apache log level for this virtual host. If not provided,
                default to 'info'.
    - hostname: the name of this vhost.
    - enable_compression: (optional) output directives to use the deflate module
                          (default to False).
    - tls: a tuple containing path to the private and public key. If not
           provided, only HTTP configuration is produced.
           An optional third value can be used to indicate the CA certificate
           file path.
           Note that these path are not taken relative to the PREFIX, since
           keys must NOT be present there.

    Note that the configuration file will be created in PREFIX; a symlink to it
    in the appropriate apache configuration directory is a good idea.

    For aliases, cache strategy can be either "no-cache" to explicitely mark all
    files to expire as soon as they are available, or "cache" to mark them to be
    cached (this is done by setting their expiration date at a month after
    access).
    """
    cgiName = 'cgi/wsgi.py'
    runTask({'name': 'cgi',
             'desc': 'Create WSGI script',
             'args': {'path': cgiName},
             })
    fullCGIPath = join(config().PREFIX, cgiName)
    apacheFullPath = join(config().PREFIX, name)
    apacheFullDir = dirname(apacheFullPath)
    utils.real_mkdir(apacheFullDir)

    if 'hostname' not in apacheConfig:
        apacheConfig['hostname'] = 'localhost'

    if 'loglevel' not in apacheConfig:
        apacheConfig['loglevel'] = 'info'

    if 'enable_compression' not in apacheConfig:
        apacheConfig['enable_compression'] = False

    if 'tls' not in apacheConfig:
        apacheConfig['tls'] = None

    if 'alias' not in apacheConfig:
        apacheConfig['alias'] = []

    with utils.open_utf8(apacheFullPath, 'w') as outFile:
        _writeVHost(outFile,
                    fullCGIPath,
                    apacheConfig,
                    )
    utils.cfg_chown(apacheFullPath)
    utils.cfg_chmod(apacheFullPath)


def apacheGrantAccess(outFile, directory, cacheStrategy=None):
    """Write an all-access directive to a directory in an apache config dir."""
    outFile.write('<Directory %s>\n' % join(config().PREFIX, directory))
    outFile.write('Require all granted\n')
    if cacheStrategy:
        cacheStrategy = cacheStrategy.lower()
        outFile.write('ExpiresActive "on"\n')
        if cacheStrategy == 'no-cache':
            outFile.write('ExpiresDefault "access"\n')
        elif cacheStrategy == 'cache':
            outFile.write('ExpiresDefault "access plus 1 month"\n')
        else:
            raise RuntimeError('Invalid cache strategy: "%s"' % cacheStrategy)
    outFile.write('</Directory>\n')
