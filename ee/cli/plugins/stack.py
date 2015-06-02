"""Stack Plugin for EasyEngine."""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.core.download import EEDownload
from ee.core.shellexec import EEShellExec
from ee.core.fileutils import EEFileUtils
from ee.core.apt_repo import EERepo
from ee.core.extract import EEExtract
from ee.core.mysql import EEMysql
from ee.core.addswap import EESwap
from ee.core.git import EEGit
from ee.core.checkfqdn import check_fqdn
from pynginxconfig import NginxConfig
from ee.core.services import EEService
from ee.core.variables import EEVariables
import random
import string
import configparser
import time
import shutil
import os
import pwd
import grp
import codecs
import platform
from ee.cli.plugins.stack_services import EEStackStatusController
from ee.cli.plugins.stack_migrate import EEStackMigrateController
from ee.cli.plugins.stack_upgrade import EEStackUpgradeController
from ee.core.logging import Log

def ee_stack_hook(app):
    # do something with the ``app`` object here.
    pass


class EEStackController(CementBaseController):
    class Meta:
        label = 'stack'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'Stack command manages stack operations'
        arguments = [
            (['--all'],
                dict(help='Install all stack', action='store_true')),
            (['--web'],
                dict(help='Install web stack', action='store_true')),
            (['--admin'],
                dict(help='Install admin tools stack', action='store_true')),
            (['--mail'],
                dict(help='Install mail server stack', action='store_true')),
            (['--mailscanner'],
                dict(help='Install mail scanner stack', action='store_true')),
            (['--nginx'],
                dict(help='Install Nginx stack', action='store_true')),
            (['--php'],
                dict(help='Install PHP stack', action='store_true')),
            (['--mysql'],
                dict(help='Install MySQL stack', action='store_true')),
            (['--hhvm'],
                dict(help='Install HHVM stack', action='store_true')),
            (['--postfix'],
                dict(help='Install Postfix stack', action='store_true')),
            (['--wpcli'],
                dict(help='Install WPCLI stack', action='store_true')),
            (['--phpmyadmin'],
                dict(help='Install PHPMyAdmin stack', action='store_true')),
            (['--adminer'],
                dict(help='Install Adminer stack', action='store_true')),
            (['--utils'],
                dict(help='Install Utils stack', action='store_true')),
            ]
        usage = "ee stack (command) [options]"

    @expose(hide=True)
    def default(self):
        """default action of ee stack command"""
        from ee.cli.plugins.mailstack import EEMailStack
        EEMailStack(self).install_stack()
        self.app.args.print_help()
        EEMailStack(self).purged_stack()

    
    @expose(help="Install packages")
    def install(self, packages=[], apt_packages=[], disp_msg=True):
        """Start installation of packages"""
        self.msg = []
        try:
            # Default action for stack installation
            if ((not self.app.pargs.web) and (not self.app.pargs.admin) and
               (not self.app.pargs.mail) and (not self.app.pargs.nginx) and
               (not self.app.pargs.php) and (not self.app.pargs.mysql) and
               (not self.app.pargs.postfix) and (not self.app.pargs.wpcli) and
               (not self.app.pargs.phpmyadmin) and (not self.app.pargs.hhvm)
               and
               (not self.app.pargs.adminer) and (not self.app.pargs.utils) and
               (not self.app.pargs.mailscanner) and (not self.app.pargs.all)):
                self.app.pargs.web = True
                self.app.pargs.admin = True

            if self.app.pargs.all:
                self.app.pargs.web = True
                self.app.pargs.admin = True
                self.app.pargs.mail = True

            if self.app.pargs.web:
                self.app.pargs.nginx = True
                self.app.pargs.php = True
                self.app.pargs.mysql = True
                self.app.pargs.wpcli = True
                self.app.pargs.postfix = True
                self.app.pargs.hhvm = True

            if self.app.pargs.admin:
                self.app.pargs.nginx = True
                self.app.pargs.php = True
                self.app.pargs.mysql = True
                self.app.pargs.adminer = True
                self.app.pargs.phpmyadmin = True
                self.app.pargs.utils = True

            if self.app.pargs.mail:
                self.app.pargs.nginx = True
                self.app.pargs.php = True
                self.app.pargs.mysql = True
                self.app.pargs.postfix = True

                if not EEAptGet.is_installed(self, 'dovecot-core'):
                    check_fqdn(self,
                               os.popen("hostname -f | tr -d '\n'").read())
                    Log.debug(self, "Setting apt_packages variable for mail")
                    apt_packages = apt_packages + EEVariables.ee_mail
                    packages = packages + [["https://github.com/opensolutions/"
                                            "ViMbAdmin/archive/{0}.tar.gz"
                                            .format(EEVariables.ee_vimbadmin),
                                            "/tmp/vimbadmin.tar.gz",
                                            "ViMbAdmin"],
                                           ["https://github.com/roundcube/"
                                            "roundcubemail/releases/download/"
                                            "{0}/roundcubemail-{0}.tar.gz"
                                            .format(EEVariables.ee_roundcube),
                                            "/tmp/roundcube.tar.gz",
                                            "Roundcube"]]

                    if EEVariables.ee_ram > 1024:
                        self.app.pargs.mailscanner = True
                    else:
                        Log.info(self, "System RAM is less than 1GB\nMail "
                                 "scanner packages are not going to install"
                                 " automatically")
                else:
                    Log.info(self, "Mail server is already installed")

            if self.app.pargs.nginx:
                Log.debug(self, "Setting apt_packages variable for Nginx")

                if EEVariables.ee_platform_distro == 'debian':
                    check_nginx = 'nginx-extras'
                else:
                    check_nginx = 'nginx-custom'

                if not EEAptGet.is_installed(self, check_nginx):
                    apt_packages = apt_packages + EEVariables.ee_nginx
                else:
                    Log.debug(self, "Nginx already installed")
                    Log.info(self, "Nginx already installed")
            if self.app.pargs.php:
                Log.debug(self, "Setting apt_packages variable for PHP")
                if not EEAptGet.is_installed(self, 'php5-fpm'):
                    apt_packages = apt_packages + EEVariables.ee_php
                else:
                    Log.debug(self, "PHP already installed")
                    Log.info(self, "PHP already installed")

            if self.app.pargs.hhvm:
                Log.debug(self, "Setting apt packages variable for HHVM")
                if platform.architecture()[0] is '32bit':
                    Log.error(self, "HHVM is not supported by 32bit system")
                if not EEAptGet.is_installed(self, 'hhvm'):
                    apt_packages = apt_packages + EEVariables.ee_hhvm
                else:
                    Log.debug(self, "HHVM already installed")
                    Log.info(self, "HHVM already installed")

            if self.app.pargs.mysql:
                Log.debug(self, "Setting apt_packages variable for MySQL")
                if not EEShellExec.cmd_exec(self, "mysqladmin ping"):
                    apt_packages = apt_packages + EEVariables.ee_mysql
                    packages = packages + [["https://raw."
                                            "githubusercontent.com/"
                                            "major/MySQLTuner-perl"
                                            "/master/mysqltuner.pl",
                                            "/usr/bin/mysqltuner",
                                            "MySQLTuner"]]

                else:
                    Log.debug(self, "MySQL connection is already alive")
                    Log.info(self, "MySQL connection is already alive")
            if self.app.pargs.postfix:
                Log.debug(self, "Setting apt_packages variable for Postfix")
                if not EEAptGet.is_installed(self, 'postfix'):
                    apt_packages = apt_packages + EEVariables.ee_postfix
                else:
                    Log.debug(self, "Postfix is already installed")
                    Log.info(self, "Postfix is already installed")
            if self.app.pargs.wpcli:
                Log.debug(self, "Setting packages variable for WP-CLI")
                if not EEShellExec.cmd_exec(self, "which wp"):
                    packages = packages + [["https://github.com/wp-cli/wp-cli/"
                                            "releases/download/v{0}/"
                                            "wp-cli-{0}.phar"
                                            "".format(EEVariables.ee_wp_cli),
                                            "/usr/bin/wp",
                                            "WP-CLI"]]
                else:
                    Log.debug(self, "WP-CLI is already installed")
                    Log.info(self, "WP-CLI is already installed")
            if self.app.pargs.phpmyadmin:
                Log.debug(self, "Setting packages varible for phpMyAdmin ")
                packages = packages + [["https://github.com/phpmyadmin/"
                                        "phpmyadmin/archive/STABLE.tar.gz",
                                        "/tmp/pma.tar.gz", "phpMyAdmin"]]

            if self.app.pargs.adminer:
                Log.debug(self, "Setting packages variable for Adminer ")
                packages = packages + [["http://downloads.sourceforge.net/"
                                        "adminer/adminer-{0}.php"
                                        "".format(EEVariables.ee_adminer),
                                        "{0}22222/"
                                        "htdocs/db/adminer/index.php"
                                        .format(EEVariables.ee_webroot),
                                        "Adminer"]]

            if self.app.pargs.mailscanner:
                if not EEAptGet.is_installed(self, 'amavisd-new'):
                    if (EEAptGet.is_installed(self, 'dovecot-core') or
                       self.app.pargs.mail):
                        apt_packages = (apt_packages +
                                        EEVariables.ee_mailscanner)
                    else:
                        Log.error(self, "Failed to find installed Dovecot")
                else:
                    Log.error(self, "Mail scanner already installed")

            if self.app.pargs.utils:
                Log.debug(self, "Setting packages variable for utils")
                packages = packages + [["http://phpmemcacheadmin.googlecode"
                                        ".com/files/phpMemcachedAdmin-1.2.2"
                                        "-r262.tar.gz", '/tmp/memcache.tar.gz',
                                        'phpMemcachedAdmin'],
                                       ["https://raw.githubusercontent.com"
                                        "/rtCamp/eeadmin/master/cache/nginx/"
                                        "clean.php",
                                        "{0}22222/htdocs/cache/"
                                        "nginx/clean.php"
                                        .format(EEVariables.ee_webroot),
                                        "clean.php"],
                                       ["https://raw.github.com/rlerdorf/"
                                        "opcache-status/master/opcache.php",
                                        "{0}22222/htdocs/cache/"
                                        "opcache/opcache.php"
                                        .format(EEVariables.ee_webroot),
                                        "opcache.php"],
                                       ["https://raw.github.com/amnuts/"
                                        "opcache-gui/master/index.php",
                                        "{0}22222/htdocs/"
                                        "cache/opcache/opgui.php"
                                        .format(EEVariables.ee_webroot),
                                        "Opgui"],
                                       ["https://gist.github.com/ck-on/4959032"
                                        "/raw/0b871b345fd6cfcd6d2be030c1f33d1"
                                        "ad6a475cb/ocp.php",
                                        "{0}22222/htdocs/cache/"
                                        "opcache/ocp.php"
                                        .format(EEVariables.ee_webroot),
                                        "OCP.php"],
                                       ["https://github.com/jokkedk/webgrind/"
                                        "archive/master.tar.gz",
                                        '/tmp/webgrind.tar.gz', 'Webgrind'],
                                       ["http://bazaar.launchpad.net/~"
                                        "percona-toolkit-dev/percona-toolkit/"
                                        "2.1/download/head:/ptquerydigest-"
                                        "20110624220137-or26tn4"
                                        "expb9ul2a-16/pt-query-digest",
                                        "/usr/bin/pt-query-advisor",
                                        "pt-query-advisor"],
                                       ["https://github.com/box/Anemometer/"
                                        "archive/master.tar.gz",
                                        '/tmp/anemometer.tar.gz', 'Anemometer']
                                       ]
        except Exception as e:
            pass

        if len(apt_packages) or len(packages):
            Log.debug(self, "Calling pre_pref")
            self.pre_pref(apt_packages)
            if len(apt_packages):
                EESwap.add(self)
                Log.info(self, "Updating apt-cache, please wait...")
                EEAptGet.update(self)
                Log.info(self, "Installing packages, please wait...")
                EEAptGet.install(self, apt_packages)
            if len(packages):
                Log.debug(self, "Downloading following: {0}".format(packages))
                EEDownload.download(self, packages)
            Log.debug(self, "Calling post_pref")
            self.post_pref(apt_packages, packages)
            if disp_msg:
                if len(self.msg):
                    for msg in self.msg:
                        Log.info(self, Log.ENDC + msg)
                Log.info(self, "Successfully installed packages")
            else:
                return self.msg

    @expose(help="Remove packages")
    def remove(self):
        """Start removal of packages"""
        apt_packages = []
        packages = []

        # Default action for stack remove
        if ((not self.app.pargs.web) and (not self.app.pargs.admin) and
           (not self.app.pargs.mail) and (not self.app.pargs.nginx) and
           (not self.app.pargs.php) and (not self.app.pargs.mysql) and
           (not self.app.pargs.postfix) and (not self.app.pargs.wpcli) and
           (not self.app.pargs.phpmyadmin) and (not self.app.pargs.hhvm) and
           (not self.app.pargs.adminer) and (not self.app.pargs.utils) and
           (not self.app.pargs.mailscanner) and (not self.app.pargs.all)):
            self.app.pargs.web = True
            self.app.pargs.admin = True

        if self.app.pargs.all:
            self.app.pargs.web = True
            self.app.pargs.admin = True
            self.app.pargs.mail = True

        if self.app.pargs.web:
            self.app.pargs.nginx = True
            self.app.pargs.php = True
            self.app.pargs.hhvm = True
            self.app.pargs.mysql = True
            self.app.pargs.wpcli = True
            self.app.pargs.postfix = True

        if self.app.pargs.admin:
            self.app.pargs.adminer = True
            self.app.pargs.phpmyadmin = True
            self.app.pargs.utils = True

        if self.app.pargs.mail:
            Log.debug(self, "Removing mail server packages")
            apt_packages = apt_packages + EEVariables.ee_mail
            apt_packages = apt_packages + EEVariables.ee_mailscanner
            packages = packages + ["{0}22222/htdocs/vimbadmin"
                                   .format(EEVariables.ee_webroot),
                                   "{0}roundcubemail"
                                   .format(EEVariables.ee_webroot)]
            if EEShellExec.cmd_exec(self, "mysqladmin ping"):
                EEMysql.execute(self, "drop database IF EXISTS vimbadmin")
                EEMysql.execute(self, "drop database IF EXISTS roundcubemail")

        if self.app.pargs.mailscanner:
            apt_packages = (apt_packages + EEVariables.ee_mailscanner)

        if self.app.pargs.nginx:
            Log.debug(self, "Removing apt_packages variable of Nginx")
            apt_packages = apt_packages + EEVariables.ee_nginx
        if self.app.pargs.php:
            Log.debug(self, "Removing apt_packages variable of PHP")
            apt_packages = apt_packages + EEVariables.ee_php

        if self.app.pargs.hhvm:
            if EEAptGet.is_installed(self, 'hhvm'):
                Log.debug(self, "Removing apt_packages varible of HHVM")
                apt_packages = apt_packages + EEVariables.ee_hhvm

        if self.app.pargs.mysql:
            Log.debug(self, "Removing apt_packages variable of MySQL")
            apt_packages = apt_packages + EEVariables.ee_mysql
            packages = packages + ['/usr/bin/mysqltuner']
        if self.app.pargs.postfix:
            Log.debug(self, "Removing apt_packages variable of Postfix")
            apt_packages = apt_packages + EEVariables.ee_postfix
        if self.app.pargs.wpcli:
            Log.debug(self, "Removing package variable of WPCLI ")
            packages = packages + ['/usr/bin/wp']
        if self.app.pargs.phpmyadmin:
            Log.debug(self, "Removing package variable of phpMyAdmin ")
            packages = packages + ['{0}22222/htdocs/db/pma'
                                   .format(EEVariables.ee_webroot)]
        if self.app.pargs.adminer:
            Log.debug(self, "Removing package variable of Adminer ")
            packages = packages + ['{0}22222/htdocs/db/adminer'
                                   .format(EEVariables.ee_webroot)]
        if self.app.pargs.utils:
            Log.debug(self, "Removing package variable of utils ")
            packages = packages + ['{0}22222/htdocs/php/webgrind/'
                                   .format(EEVariables.ee_webroot),
                                   '{0}22222/htdocs/cache/opcache'
                                   .format(EEVariables.ee_webroot),
                                   '{0}22222/htdocs/cache/nginx/'
                                   'clean.php'.format(EEVariables.ee_webroot),
                                   '{0}22222/htdocs/cache/memcache'
                                   .format(EEVariables.ee_webroot),
                                   '/usr/bin/pt-query-advisor',
                                   '{0}22222/htdocs/db/anemometer'
                                   .format(EEVariables.ee_webroot)]
        ee_prompt = input('Are you sure you to want to'
                          ' purge  from server.'
                          'Package configuration will remain'
                          ' on server after this operation.\n'
                          'Any answer other than '
                          '"yes" will be stop this'
                          ' operation :  ')

        if len(apt_packages):
            if ee_prompt == 'YES' or ee_prompt == 'yes':
                Log.debug(self, "Removing apt_packages")
                Log.info(self, "Removing packages, please wait...")
                EEAptGet.remove(self, apt_packages)
                EEAptGet.auto_remove(self)

        if len(packages):
            if ee_prompt == 'YES' or ee_prompt == 'yes':
                EEFileUtils.remove(self, packages)
                EEAptGet.auto_remove(self)

        if ee_prompt == 'YES' or ee_prompt == 'yes':
            Log.info(self, "Successfully removed packages")

    @expose(help="Purge packages")
    def purge(self):
        """Start purging of packages"""
        apt_packages = []
        packages = []

        # Default action for stack purge
        if ((not self.app.pargs.web) and (not self.app.pargs.admin) and
           (not self.app.pargs.mail) and (not self.app.pargs.nginx) and
           (not self.app.pargs.php) and (not self.app.pargs.mysql) and
           (not self.app.pargs.postfix) and (not self.app.pargs.wpcli) and
           (not self.app.pargs.phpmyadmin) and (not self.app.pargs.hhvm) and
           (not self.app.pargs.adminer) and (not self.app.pargs.utils) and
           (not self.app.pargs.mailscanner) and (not self.app.pargs.all)):
            self.app.pargs.web = True
            self.app.pargs.admin = True

        if self.app.pargs.all:
            self.app.pargs.web = True
            self.app.pargs.admin = True
            self.app.pargs.mail = True

        if self.app.pargs.web:
            self.app.pargs.nginx = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True
            self.app.pargs.wpcli = True
            self.app.pargs.postfix = True
            self.app.pargs.hhvm = True

        if self.app.pargs.admin:
            self.app.pargs.adminer = True
            self.app.pargs.phpmyadmin = True
            self.app.pargs.utils = True

        if self.app.pargs.mail:
            Log.debug(self, "Removing mail server packages")
            apt_packages = apt_packages + EEVariables.ee_mail
            apt_packages = apt_packages + EEVariables.ee_mailscanner
            packages = packages + ["{0}22222/htdocs/vimbadmin"
                                   .format(EEVariables.ee_webroot),
                                   "{0}roundcubemail"
                                   .format(EEVariables.ee_webroot)]
            if EEShellExec.cmd_exec(self, "mysqladmin ping"):
                EEMysql.execute(self, "drop database IF EXISTS vimbadmin")
                EEMysql.execute(self, "drop database IF EXISTS roundcubemail")

        if self.app.pargs.mailscanner:
            apt_packages = (apt_packages + EEVariables.ee_mailscanner)

        if self.app.pargs.nginx:
            Log.debug(self, "Purge apt_packages variable of Nginx")
            apt_packages = apt_packages + EEVariables.ee_nginx
        if self.app.pargs.php:
            Log.debug(self, "Purge apt_packages variable PHP")
            apt_packages = apt_packages + EEVariables.ee_php
        if self.app.pargs.hhvm:
            if EEAptGet.is_installed(self, 'hhvm'):
                Log.debug(self, "Removing apt_packages varible of HHVM")
                apt_packages = apt_packages + EEVariables.ee_hhvm
        if self.app.pargs.mysql:
            Log.debug(self, "Purge apt_packages variable MySQL")
            apt_packages = apt_packages + EEVariables.ee_mysql
            packages = packages + ['/usr/bin/mysqltuner']
        if self.app.pargs.postfix:
            Log.debug(self, "Purge apt_packages variable PostFix")
            apt_packages = apt_packages + EEVariables.ee_postfix
        if self.app.pargs.wpcli:
            Log.debug(self, "Purge package variable WPCLI")
            packages = packages + ['/usr/bin/wp']
        if self.app.pargs.phpmyadmin:
            packages = packages + ['{0}22222/htdocs/db/pma'.
                                   format(EEVariables.ee_webroot)]
            Log.debug(self, "Purge package variable phpMyAdmin")
        if self.app.pargs.adminer:
            Log.debug(self, "Purge  package variable Adminer")
            packages = packages + ['{0}22222/htdocs/db/adminer'
                                   .format(EEVariables.ee_webroot)]
        if self.app.pargs.utils:
            Log.debug(self, "Purge package variable utils")
            packages = packages + ['{0}22222/htdocs/php/webgrind/'
                                   .format(EEVariables.ee_webroot),
                                   '{0}22222/htdocs/cache/opcache'
                                   .format(EEVariables.ee_webroot),
                                   '{0}22222/htdocs/cache/nginx/'
                                   'clean.php'.format(EEVariables.ee_webroot),
                                   '{0}22222/htdocs/cache/memcache'
                                   .format(EEVariables.ee_webroot),
                                   '/usr/bin/pt-query-advisor',
                                   '{0}22222/htdocs/db/anemometer'
                                   .format(EEVariables.ee_webroot)
                                   ]

        ee_prompt = input('Are you sure you to want to purge '
                          'from server '
                          'alongwith their configuration'
                          ' packages,\nAny answer other than '
                          '"yes" will be stop this '
                          'operation :')

        if len(apt_packages):
            if ee_prompt == 'YES' or ee_prompt == 'yes':
                Log.info(self, "Purging packages, please wait...")
                EEAptGet.remove(self, apt_packages, purge=True)
                EEAptGet.auto_remove(self)

        if len(packages):
            if ee_prompt == 'YES' or ee_prompt == 'yes':
                EEFileUtils.remove(self, packages)
                EEAptGet.auto_remove(self)

        if ee_prompt == 'YES' or ee_prompt == 'yes':
            Log.info(self, "Successfully purged packages")


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(EEStackController)
    handler.register(EEStackStatusController)
    handler.register(EEStackMigrateController)
    handler.register(EEStackUpgradeController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', ee_stack_hook)
