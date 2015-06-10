import os
import sys
import random
import string
import codecs
import configparser
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.core.apt_repo import EERepo
from ee.cli.plugins.eestack import EEStack
from ee.core.shellexec import EEShellExec
from ee.core.shellexec import CommandExecutionError
from ee.core.fileutils import EEFileUtils
from ee.core.git import EEGit
from ee.core.services import EEService
from ee.core.logging import Log
from ee.cli.main import app


class EEPhpStack(EEStack):
    """
        EasyEngine PHP stack
    """
    packages_name = EEVariables.ee_php
    app = app
    log = app.log

    def __init__(self, packages_name=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        """

        self.packages_name = self._get_stack()  
        super(EEPhpStack, self).__init__(self.packages_name)

    def _get_stack(self):
        return EEPhpStack.packages_name

    def _add_repo(self):
        """
          Add repository for packages to be downloaded from
        """
        self.log.info("Adding PHP repository, please wait...")
        if EEVariables.ee_platform_distro == 'debian':
            if EEVariables.ee_platform_codename != 'jessie':
                self.log.debug(self, 'Adding repo_url of php for debian')
                EERepo.add(self, repo_url=EEVariables.ee_php_repo)
                self.log.debug(self, 'Adding Dotdeb/php GPG key')
                EERepo.add_key(self, '89DF5277')
            else:
                self.log.debug(self, 'Adding ppa for PHP')
                EERepo.add(self, ppa=EEVariables.ee_php_repo)
        EEAptGet.update(self)

    def _pre_install_stack(self):
        """
        Defines pre-install activities done before installing php stack
        """
        # Add php repository
        self._add_repo()

    def _post_install_stack(self):
        """
        Defines activities done after installing php stack
        """
        # Create log directories
        if not os.path.exists('/var/log/php5/'):
            self.log.debug(self, 'Creating directory /var/log/php5/')
            os.makedirs('/var/log/php5/')

        # For debian install xdebug

        if (EEVariables.ee_platform_distro == "debian" and
           EEVariables.ee_platform_codename == 'wheezy'):
            EEShellExec.cmd_exec(self, "pecl install xdebug")

            with open("/etc/php5/mods-available/xdebug.ini",
                      encoding='utf-8', mode='a') as myfile:
                myfile.write("zend_extension=/usr/lib/php5/20131226/"
                             "xdebug.so\n")

            EEFileUtils.create_symlink(self, ["/etc/php5/"
                                       "mods-available/xdebug.ini",
                                              "/etc/php5/fpm/conf.d"
                                              "/20-xedbug.ini"])

        # Parse etc/php5/fpm/php.ini
        config = configparser.ConfigParser()
        self.log.debug(self, "configuring php file /etc/php5/fpm/php.ini")
        config.read('/etc/php5/fpm/php.ini')
        config['PHP']['expose_php'] = 'Off'
        config['PHP']['post_max_size'] = '100M'
        config['PHP']['upload_max_filesize'] = '100M'
        config['PHP']['max_execution_time'] = '300'
        config['PHP']['date.timezone'] = EEVariables.ee_timezone
        with open('/etc/php5/fpm/php.ini',
                  encoding='utf-8', mode='w') as configfile:
            self.log.debug(self, "Writting php configuration into "
                      "/etc/php5/fpm/php.ini")
            config.write(configfile)

        # Prase /etc/php5/fpm/php-fpm.conf
        config = configparser.ConfigParser()
        self.log.debug(self, "configuring php file"
                  "/etc/php5/fpm/php-fpm.conf")
        config.read_file(codecs.open("/etc/php5/fpm/php-fpm.conf",
                                     "r", "utf8"))
        config['global']['error_log'] = '/var/log/php5/fpm.log'
        config.remove_option('global', 'include')
        config['global']['log_level'] = 'notice'
        config['global']['include'] = '/etc/php5/fpm/pool.d/*.conf'
        with codecs.open('/etc/php5/fpm/php-fpm.conf',
                         encoding='utf-8', mode='w') as configfile:
            self.log.debug(self, "writting php5 configuration into "
                      "/etc/php5/fpm/php-fpm.conf")
            config.write(configfile)

        # Parse /etc/php5/fpm/pool.d/www.conf
        config = configparser.ConfigParser()
        config.read_file(codecs.open('/etc/php5/fpm/pool.d/www.conf',
                                     "r", "utf8"))
        config['www']['ping.path'] = '/ping'
        config['www']['pm.status_path'] = '/status'
        config['www']['pm.max_requests'] = '500'
        config['www']['pm.max_children'] = '100'
        config['www']['pm.start_servers'] = '20'
        config['www']['pm.min_spare_servers'] = '10'
        config['www']['pm.max_spare_servers'] = '30'
        config['www']['request_terminate_timeout'] = '300'
        config['www']['pm'] = 'ondemand'
        config['www']['listen'] = '127.0.0.1:9000'
        with codecs.open('/etc/php5/fpm/pool.d/www.conf',
                         encoding='utf-8', mode='w') as configfile:
            self.log.debug(self, "writting PHP5 configuration into "
                      "/etc/php5/fpm/pool.d/www.conf")
            config.write(configfile)

        # Generate /etc/php5/fpm/pool.d/debug.conf
        EEFileUtils.copyfile(self, "/etc/php5/fpm/pool.d/www.conf",
                             "/etc/php5/fpm/pool.d/debug.conf")
        EEFileUtils.searchreplace(self, "/etc/php5/fpm/pool.d/"
                                  "debug.conf", "[www]", "[debug]")
        config = configparser.ConfigParser()
        config.read('/etc/php5/fpm/pool.d/debug.conf')
        config['debug']['listen'] = '127.0.0.1:9001'
        config['debug']['rlimit_core'] = 'unlimited'
        config['debug']['slowlog'] = '/var/log/php5/slow.log'
        config['debug']['request_slowlog_timeout'] = '10s'
        with open('/etc/php5/fpm/pool.d/debug.conf',
                  encoding='utf-8', mode='w') as confifile:
            self.log.debug(self, "writting PHP5 configuration into "
                      "/etc/php5/fpm/pool.d/debug.conf")
            config.write(confifile)

        with open("/etc/php5/fpm/pool.d/debug.conf",
                  encoding='utf-8', mode='a') as myfile:
            myfile.write("php_admin_value[xdebug.profiler_output_dir] "
                         "= /tmp/ \nphp_admin_value[xdebug.profiler_"
                         "output_name] = cachegrind.out.%p-%H-%R "
                         "\nphp_admin_flag[xdebug.profiler_enable"
                         "_trigger] = on \nphp_admin_flag[xdebug."
                         "profiler_enable] = off\n")

        # Disable xdebug
        EEFileUtils.searchreplace(self, "/etc/php5/mods-available/"
                                  "xdebug.ini",
                                  "zend_extension",
                                  ";zend_extension")

        # PHP and Debug pull configuration
        if not os.path.exists('{0}22222/htdocs/fpm/status/'
                              .format(EEVariables.ee_webroot)):
            self.log.debug(self, 'Creating directory '
                      '{0}22222/htdocs/fpm/status/ '
                      .format(EEVariables.ee_webroot))
            os.makedirs('{0}22222/htdocs/fpm/status/'
                        .format(EEVariables.ee_webroot))
        open('{0}22222/htdocs/fpm/status/debug'
             .format(EEVariables.ee_webroot),
             encoding='utf-8', mode='a').close()
        open('{0}22222/htdocs/fpm/status/php'
             .format(EEVariables.ee_webroot),
             encoding='utf-8', mode='a').close()

        # Write info.php
        if not os.path.exists('{0}22222/htdocs/php/'
                              .format(EEVariables.ee_webroot)):
            self.log.debug(self, 'Creating directory '
                      '{0}22222/htdocs/php/ '
                      .format(EEVariables.ee_webroot))
            os.makedirs('{0}22222/htdocs/php'
                        .format(EEVariables.ee_webroot))

        with open("{0}22222/htdocs/php/info.php"
                  .format(EEVariables.ee_webroot),
                  encoding='utf-8', mode='w') as myfile:
            myfile.write("<?php\nphpinfo();\n?>")

        EEFileUtils.chown(self, "{0}22222"
                          .format(EEVariables.ee_webroot),
                          EEVariables.ee_php_user,
                          EEVariables.ee_php_user, recursive=True)

        EEGit.add(self, ["/etc/php5"], msg="Adding PHP into Git")
        EEService.restart_service(self, 'php5-fpm')


    def install_stack(self):
        """
        Install PHP stack
        """
        if not self.is_installed():
          self.log.info("Installing PHP stack, please wait...")
          self._pre_install_stack()
          super(EEPhpStack, self).install_stack()
          self._post_install_stack()

    def remove_stack(self):
        """
        Remove PHP stack
        """
        self.log.info("Removing PHP stack, please wait...")
        super(EEPhpStack, self).remove_stack()

    def purge_stack(self):
        self.log.info("Purging PHP stack, please wait...")
        super(EEPhpStack, self).purge_stack()

    def is_installed(self):
        self.log.info("Checking if php5-fpm is installed")
        return EEAptGet.is_installed(self, 'php5-fpm')