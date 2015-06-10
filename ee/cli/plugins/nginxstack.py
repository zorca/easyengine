import os
import sys
import random
import string
import configparser
from pynginxconfig import NginxConfig
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.core.apt_repo import EERepo
from ee.core.fileutils import EEFileUtils
from ee.core.git import EEGit
from ee.cli.plugins.eestack import EEStack
from ee.core.shellexec import EEShellExec
from ee.core.services import EEService
from ee.core.shellexec import CommandExecutionError
from ee.core.logging import Log
from ee.cli.main import app


class EENginxStack(EEStack):
    """
        EasyEngine NGINX stack
    """
    packages_name = EEVariables.ee_nginx
    app = app
    log = app.log


    def __init__(self, packages_name=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        """

        self.packages_name = self._get_stack()
        self.http_auth_user = 'easyengine'
        self.http_auth_pass =  (''.join([random.choice
                                (string.ascii_letters + string.digits)
                                for n in range(6)]))
        super(EENginxStack, self).__init__(self.packages_name)

    def _get_stack(self):
        return EENginxStack.packages_name

    def _add_repo(self):
        """
          Add repository for packages to be downloaded from
        """
        self.log.info("Adding NGINX repository, please wait...")
        if EEVariables.ee_platform_distro == 'debian':
            self.log.debug(self, 'Adding Dotdeb/nginx GPG key')
            EERepo.add(self, repo_url=EEVariables.ee_nginx_repo)
        else:
            EERepo.add(self, ppa=EEVariables.ee_nginx_repo)
            self.log.debug(self, 'Adding ppa of NGINX')
        EEAptGet.update(self)

    def _pre_install_stack(self):
        """
        Defines pre-install activities done before installing nginx stack
        """
        # Add Nginx repository
        self._add_repo()

    def _post_install_stack(self):
        """
        Defines activities done after installing nginx stack
        """
        self.log.debug("Running post install, please wait...")

        if ((not EEShellExec.cmd_exec(self, "grep -q -Hr EasyEngine "
            "/etc/nginx")) and os.path.isfile('/etc/nginx/nginx.conf')):
            nc = NginxConfig()
            self.log.debug(self, 'Loading file /etc/nginx/nginx.conf ')
            nc.loadf('/etc/nginx/nginx.conf')
            nc.set('worker_processes', 'auto')
            nc.append(('worker_rlimit_nofile', '100000'), position=2)
            nc.remove(('events', ''))
            nc.append({'name': 'events', 'param': '', 'value':
                      [('worker_connections', '4096'),
                       ('multi_accept', 'on')]}, position=4)
            nc.set([('http',), 'keepalive_timeout'], '30')
            self.log.debug(self, "Writting nginx configuration to "
                           "file /etc/nginx/nginx.conf ")
            nc.savef('/etc/nginx/nginx.conf')

            # Custom Nginx configuration by EasyEngine
            if EEVariables.ee_platform_distro == 'ubuntu':
                data = dict(version=EEVariables.ee_version,
                            Ubuntu=True)
            else:
                data = dict(version=EEVariables.ee_version,
                            Debian=True)
            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/conf.d/ee-nginx.conf ')
            ee_nginx = open('/etc/nginx/conf.d/ee-nginx.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'nginx-core.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            data = dict()
            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/conf.d/blockips.conf')
            ee_nginx = open('/etc/nginx/conf.d/blockips.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'blockips.mustache', out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/conf.d/fastcgi.conf')
            ee_nginx = open('/etc/nginx/conf.d/fastcgi.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'fastcgi.mustache', out=ee_nginx)
            ee_nginx.close()

            data = dict(php="9000", debug="9001", hhvm="8000")
            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/conf.d/upstream.conf ')
            ee_nginx = open('/etc/nginx/conf.d/upstream.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'upstream.mustache', out=ee_nginx)
            ee_nginx.close()

            # Setup Nginx common directory
            if not os.path.exists('/etc/nginx/common'):
                self.log.debug(self, 'Creating directory'
                               '/etc/nginx/common')
                os.makedirs('/etc/nginx/common')

            data = dict(webroot=EEVariables.ee_webroot)
            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/acl.conf')
            ee_nginx = open('/etc/nginx/common/acl.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'acl.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/locations.conf')
            ee_nginx = open('/etc/nginx/common/locations.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'locations.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/php-hhvm.conf')
            ee_nginx = open('/etc/nginx/common/php-hhvm.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'php-hhvm.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/w3tc-hhvm.conf')
            ee_nginx = open('/etc/nginx/common/w3tc-hhvm.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'w3tc-hhvm.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/wpfc-hhvm.conf')
            ee_nginx = open('/etc/nginx/common/wpfc-hhvm.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'wpfc-hhvm.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/wpsc-hhvm.conf')
            ee_nginx = open('/etc/nginx/common/wpsc-hhvm.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'wpsc-hhvm.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/php.conf')
            ee_nginx = open('/etc/nginx/common/php.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'php.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/w3tc.conf')
            ee_nginx = open('/etc/nginx/common/w3tc.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'w3tc.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/wpcommon.conf')
            ee_nginx = open('/etc/nginx/common/wpcommon.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'wpcommon.mustache',
                       out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/wpfc.conf')
            ee_nginx = open('/etc/nginx/common/wpfc.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'wpfc.mustache',
                       out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/wpsc.conf')
            ee_nginx = open('/etc/nginx/common/wpsc.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'wpsc.mustache',
                       out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/common/wpsubdir.conf')
            ee_nginx = open('/etc/nginx/common/wpsubdir.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'wpsubdir.mustache',
                       out=ee_nginx)
            ee_nginx.close()

            # Fix whitescreen of death beacuse of missing value
            # fastcgi_param SCRIPT_FILENAME $request_filename; in file
            # /etc/nginx/fastcgi_params

            if not EEFileUtils.grep(self, '/etc/nginx/fastcgi_params',
                                    'SCRIPT_FILENAME'):
                with open('/etc/nginx/fastcgi_params',
                          encoding='utf-8', mode='a') as ee_nginx:
                    ee_nginx.write('fastcgi_param \tSCRIPT_FILENAME '
                                   '\t$request_filename;\n')

            # Pagespeed configuration
            self.log.debug(self, 'Writting the Pagespeed Global '
                           'configuration to file /etc/nginx/conf.d/'
                           'pagespeed.conf')
            ee_nginx = open('/etc/nginx/conf.d/pagespeed.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'pagespeed-global.mustache',
                       out=ee_nginx)
            ee_nginx.close()

            # 22222 port settings
            self.log.debug(self, 'Writting the nginx configuration to '
                           'file /etc/nginx/sites-available/'
                           '22222')
            ee_nginx = open('/etc/nginx/sites-available/22222',
                            encoding='utf-8', mode='w')
            app.render((data), '22222.mustache',
                        out=ee_nginx)
            ee_nginx.close()

            try:
                EEShellExec.cmd_exec(self, "printf \"{user}:"
                                     "$(openssl passwd -crypt "
                                     "{password} 2> /dev/null)\n\""
                                     "> /etc/nginx/htpasswd-ee "
                                     "2>/dev/null"
                                     .format(user=self.http_auth_user, 
                                             password=self.http_auth_pass))
            except CommandExecutionError as e:
                self.log.error(self, "Failed to save HTTP Auth")

            # Create Symbolic link for 22222
            EEFileUtils.create_symlink(self, ['/etc/nginx/'
                                              'sites-available/'
                                              '22222',
                                              '/etc/nginx/'
                                              'sites-enabled/'
                                              '22222'])
            # Create log and cert folder and softlinks
            if not os.path.exists('{0}22222/logs'
                                  .format(EEVariables.ee_webroot)):
                self.log.debug(self, "Creating directory "
                               "{0}22222/logs "
                               .format(EEVariables.ee_webroot))
                os.makedirs('{0}22222/logs'
                            .format(EEVariables.ee_webroot))

            if not os.path.exists('{0}22222/cert'
                                  .format(EEVariables.ee_webroot)):
                self.log.debug(self, "Creating directory "
                               "{0}22222/cert"
                                .format(EEVariables.ee_webroot))
                os.makedirs('{0}22222/cert'
                            .format(EEVariables.ee_webroot))

            EEFileUtils.create_symlink(self, ['/var/log/nginx/'
                                              '22222.access.log',
                                              '{0}22222/'
                                              'logs/access.log'
                                       .format(EEVariables.ee_webroot)]
                                       )

            EEFileUtils.create_symlink(self, ['/var/log/nginx/'
                                              '22222.error.log',
                                              '{0}22222/'
                                              'logs/error.log'
                                       .format(EEVariables.ee_webroot)]
                                       )

            try:
                EEShellExec.cmd_exec(self, "openssl genrsa -out "
                                     "{0}22222/cert/22222.key 2048"
                                     .format(EEVariables.ee_webroot))
                EEShellExec.cmd_exec(self, "openssl req -new -batch  "
                                     "-subj /commonName=127.0.0.1/ "
                                     "-key {0}22222/cert/22222.key "
                                     "-out {0}22222/cert/"
                                     "22222.csr"
                                     .format(EEVariables.ee_webroot))

                EEFileUtils.mvfile(self, "{0}22222/cert/22222.key"
                                   .format(EEVariables.ee_webroot),
                                   "{0}22222/cert/"
                                   "22222.key.org"
                                   .format(EEVariables.ee_webroot))

                EEShellExec.cmd_exec(self, "openssl rsa -in "
                                     "{0}22222/cert/"
                                     "22222.key.org -out "
                                     "{0}22222/cert/22222.key"
                                     .format(EEVariables.ee_webroot))

                EEShellExec.cmd_exec(self, "openssl x509 -req -days "
                                     "3652 -in {0}22222/cert/"
                                     "22222.csr -signkey {0}"
                                     "22222/cert/22222.key -out "
                                     "{0}22222/cert/22222.crt"
                                     .format(EEVariables.ee_webroot))

            except CommandExecutionError as e:
                self.log.error(self, "Failed to generate SSL for 22222")

            # Nginx Configation into GIT
            EEGit.add(self,
                      ["/etc/nginx"], msg="Adding Nginx into Git")
            EEService.reload_service(self, 'nginx')


            # self.msg = (self.msg + ["HTTP Auth User Name: easyengine"]
            #             + ["HTTP Auth Password : {0}".format(passwd)])


    def install_stack(self):
        """
        Install NGINX stack
        """
        if not self.is_installed():
            self.log.info("Installing NGINX stack, please wait...")
            self._pre_install_stack()
            super(EENginxStack, self).install_stack()
            self._post_install_stack()
            return (self.http_auth_user, self.http_auth_pass)


    def remove_stack(self):
        """
        Remove NGINX stack
        """
        self.log.info("Removing NGINX stack, please wait...")
        super(EENginxStack, self).remove_stack()

    def purge_stack(self):
        self.log.info("Purging NGINX stack, please wait...")
        super(EENginxStack, self).purge_stack()

    def is_installed(self):
        self.log.info("Checking if nginx is installed")
        return EEAptGet.is_installed(self, 'nginx-custom')
