import os
import sys
import random
import string
import shutil
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.cli.plugins.eestack import EEStack
from ee.core.shellexec import EEShellExec
from ee.core.shellexec import CommandExecutionError
from ee.core.fileutils import EEFileUtils
from ee.core.git import EEGit
from ee.core.services import EEService
from ee.cli.plugins.mysqlstack import EEMysqlStack
from ee.cli.plugins.nginxstack import EENginxStack
from ee.cli.plugins.phpstack import EEPhpStack
from ee.core.download import EEDownload
from ee.core.extract import EEExtract
from ee.core.mysql import EEMysql
from ee.cli.main import app


class EEMailStack(EEStack):
    """
        EasyEngine MAIL stack
    """
    packages_name = EEVariables.ee_mail
    app = app
    log = app.log

    def __init__(self, package_dict=None, apt_packages=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        package_url : list of urls from where packages to be fetched
        """
        self.apt_packages = apt_packages
        self.manual_packages = package_dict
        self.packages_name = self._get_stack()
        super(EEMailStack, self).__init__(self.apt_packages)

    def _get_stack(self):
        """
        """
        if self.apt_packages or self.manual_packages:
            if not self.apt_packages:
                return (self.manual_packages)
            elif not self.manual_packages:
                return (self.apt_packages)
            else:
                return (self.apt_packages, self.manual_packages)

        return EEMailStack.packages_name

    def _set_stack(self):
        """
        """
        
        if type(self.packages_name) is tuple:
            for packages in self.packages_name:
                if type(packages) is list:
                    self.apt_packages = packages
                if type(packages) is dict:
                    self.manual_packages = packages
        elif type(self.packages_name) is dict:
            self.manual_packages = self.packages_name


    def _requirement_check(self):
        """
        Check if requirements for this EEWebmailAdmin stack are fullfilled.
        """
        # Install NGINX stack if not installed
        if not EENginxStack(self).is_installed():
            self.log.info("Installing nginxstack")
            EENginxStack(self).install_stack()

        # Install PHP stack if not installed
        if not EEPhpStack(self).is_installed():
            self.log.info("Installing phpstack")
            EEPhpStack(self).install_stack()

        # Install MySQL stack if not installed
        if not EEMysqlStack(self).is_installed():
            self.log.info("Installing mysqlstack")
            EEMysqlStack(self).install_stack()
   

    def _add_repo(self):
        """
          Add repository for packages to be downloaded from
        """
        self.log.info("Adding MAIL repository, please wait...")
        # update repository information
        EEAptGet.update(self)

    def _install_vimbadmin(self, file_path):
        """

        """
        self.log.debug(self, "Extracting ViMbAdmin.tar.gz to "
                       "location {0}".format(EEVariables.ee_downloads))
        EEExtract.extract(self, file_path, EEVariables.ee_downloads)
        if not os.path.exists('{0}22222/htdocs/'
                              .format(EEVariables.ee_webroot)):
            self.log.debug(self, "Creating directory "
                      "{0}22222/htdocs/"
                      .format(EEVariables.ee_webroot))
            os.makedirs('{0}22222/htdocs/'
                        .format(EEVariables.ee_webroot))
        shutil.move('{0}ViMbAdmin-{1}/'
                    .format(EEVariables.ee_downloads, EEVariables.ee_vimbadmin),
                    '{0}22222/htdocs/vimbadmin/'
                    .format(EEVariables.ee_webroot))

        # Donwload composer and install ViMbAdmin
        self.log.debug(self, "Downloading composer "
                  "https://getcomposer.org/installer | php ")
        try:
            EEShellExec.cmd_exec(self, "cd {0}22222/htdocs"
                                 "/vimbadmin; curl"
                                 " -sS https://getcomposer.org/"
                                 "installer |"
                                 " php".format(EEVariables.ee_webroot))
            self.log.debug(self, "Installating of composer")
            EEShellExec.cmd_exec(self, "cd {0}22222/htdocs"
                                 "/vimbadmin && "
                                 "php composer.phar install "
                                 "--prefer-dist"
                                 " --no-dev && rm -f {0}22222/htdocs"
                                 "/vimbadmin/composer.phar"
                                 .format(EEVariables.ee_webroot))
        except CommandExecutionError as e:
            raise SiteError("Failed to setup ViMbAdmin")

        # Configure vimbadmin database
        vm_passwd = ''.join(random.sample(string.ascii_letters, 8))
        self.log.debug(self, "Creating vimbadmin database if not exist")
        EEMysql.execute(self, "create database if not exists"
                              " vimbadmin")
        self.log.debug(self, " grant all privileges on `vimbadmin`.* to"
                        " `vimbadmin`@`{0}` IDENTIFIED BY"
                        " ' '".format(app.config.get('mysql',
                                      'grant-host')))
        EEMysql.execute(self, "grant all privileges on `vimbadmin`.* "
                        " to `vimbadmin`@`{0}` IDENTIFIED BY"
                        " '{1}'".format(app.config.get('mysql',
                                        'grant-host'), vm_passwd),
                        errormsg="Cannot grant "
                        "user privileges", log=False)
        vm_salt = (''.join(random.sample(string.ascii_letters +
                                         string.ascii_letters, 64)))

        # Custom Vimbadmin configuration by EasyEngine
        data = dict(salt=vm_salt, host=EEVariables.ee_mysql_host,
                    password=vm_passwd,
                    php_user=EEVariables.ee_php_user)
        self.log.debug(self, 'Writting the ViMbAdmin configuration to '
                  'file {0}22222/htdocs/vimbadmin/application/'
                  'configs/application.ini'
                  .format(EEVariables.ee_webroot))
        ee_vmb = open('{0}22222/htdocs/vimbadmin/application/'
                      'configs/application.ini'
                      .format(EEVariables.ee_webroot),
                      encoding='utf-8', mode='w')
        app.render((data), 'vimbadmin.mustache',
                        out=ee_vmb)
        ee_vmb.close()

        shutil.copyfile("{0}22222/htdocs/vimbadmin/public/"
                        ".htaccess.dist"
                        .format(EEVariables.ee_webroot),
                        "{0}22222/htdocs/vimbadmin/public/"
                        ".htaccess".format(EEVariables.ee_webroot))
        self.log.debug(self, "Executing command "
                  "{0}22222/htdocs/vimbadmin/bin"
                  "/doctrine2-cli.php orm:schema-tool:"
                  "create".format(EEVariables.ee_webroot))
        try:
            EEShellExec.cmd_exec(self, "{0}22222/htdocs/vimbadmin"
                                 "/bin/doctrine2-cli.php "
                                 "orm:schema-tool:create"
                                 .format(EEVariables.ee_webroot))
        except CommandExecutionError as e:
            raise SiteError("Unable to create ViMbAdmin schema")

        EEFileUtils.chown(self, '{0}22222'
                          .format(EEVariables.ee_webroot),
                          EEVariables.ee_php_user,
                          EEVariables.ee_php_user,
                          recursive=True)

        # Copy Dovecot and Postfix templates which are depednet on
        # Vimbadmin

        if not os.path.exists('/etc/postfix/mysql/'):
            self.log.debug(self, "Creating directory "
                      "/etc/postfix/mysql/")
            os.makedirs('/etc/postfix/mysql/')

        if EEVariables.ee_mysql_host is "localhost":
            data = dict(password=vm_passwd, host="127.0.0.1")
        else:
            data = dict(password=vm_passwd,
                        host=EEVariables.ee_mysql_host)

        vm_config = open('/etc/postfix/mysql/virtual_alias_maps.cf',
                         encoding='utf-8', mode='w')
        app.render((data), 'virtual_alias_maps.mustache',
                        out=vm_config)
        vm_config.close()

        self.log.debug(self, "Writting configuration to  "
                  "/etc/postfix/mysql"
                  "/virtual_domains_maps.cf file")
        vm_config = open('/etc/postfix/mysql/virtual_domains_maps.cf',
                         encoding='utf-8', mode='w')
        app.render((data), 'virtual_domains_maps.mustache',
                        out=vm_config)
        vm_config.close()

        self.log.debug(self, "Writting configuration to "
                  "/etc/postfix/mysql"
                  "/virtual_mailbox_maps.cf file")
        vm_config = open('/etc/postfix/mysql/virtual_mailbox_maps.cf',
                         encoding='utf-8', mode='w')
        app.render((data), 'virtual_mailbox_maps.mustache',
                        out=vm_config)
        vm_config.close()

        self.log.debug(self, "Writting configration"
                        " to /etc/dovecot/dovecot-sql.conf.ext file ")
        vm_config = open('/etc/dovecot/dovecot-sql.conf.ext',
                         encoding='utf-8', mode='w')
        app.render((data), 'dovecot-sql-conf.mustache',
                        out=vm_config)
        vm_config.close()

        print("Vimbadmin Security Salt : "+ vm_salt)

    def _install_roundcube(self, file_path):
        """
        Install and configure roundcube for mailstack
        """
        # Extract RoundCubemail
        self.log.debug(self, "Extracting file {0}roundcube.tar.gz "
                  "to location {0} ".format(EEVariables.ee_downloads))
        EEExtract.extract(self, file_path, EEVariables.ee_downloads)
        if not os.path.exists('{0}roundcubemail'
                              .format(EEVariables.ee_webroot)):
            self.log.debug(self, "Creating new directory "
                      " {0}roundcubemail/"
                      .format(EEVariables.ee_webroot))
            os.makedirs('{0}roundcubemail/'
                        .format(EEVariables.ee_webroot))
        shutil.move('{0}roundcubemail-{1}/'
                    .format(EEVariables.ee_downloads, EEVariables.ee_roundcube),
                    '{0}roundcubemail/htdocs'
                    .format(EEVariables.ee_webroot))

        # Install Roundcube depednet pear packages
        EEShellExec.cmd_exec(self, "pear install Mail_Mime Net_SMTP"
                             " Mail_mimeDecode Net_IDNA2-beta "
                             "Auth_SASL Net_Sieve Crypt_GPG")

        # Configure roundcube database
        rc_passwd = ''.join(random.sample(string.ascii_letters, 8))
        self.log.debug(self, "Creating Database roundcubemail")
        EEMysql.execute(self, "create database if not exists "
                        " roundcubemail")
        self.log.debug(self, "grant all privileges"
                        " on `roundcubemail`.* to "
                        " `roundcube`@`{0}` IDENTIFIED BY "
                        "' '".format(app.config.get(
                                     'mysql', 'grant-host')))
        EEMysql.execute(self, "grant all privileges"
                        " on `roundcubemail`.* to "
                        " `roundcube`@`{0}` IDENTIFIED BY "
                        "'{1}'".format(app.config.get(
                                       'mysql', 'grant-host'),
                                       rc_passwd))
        EEShellExec.cmd_exec(self, "mysql roundcubemail < {0}"
                             "roundcubemail/htdocs/SQL/mysql"
                             ".initial.sql"
                             .format(EEVariables.ee_webroot))

        shutil.copyfile("{0}roundcubemail/htdocs/config/"
                        "config.inc.php.sample"
                        .format(EEVariables.ee_webroot),
                        "{0}roundcubemail/htdocs/config/"
                        "config.inc.php"
                        .format(EEVariables.ee_webroot))
        EEShellExec.cmd_exec(self, "sed -i \"s\'mysql://roundcube:"
                             "pass@localhost/roundcubemail\'mysql://"
                             "roundcube:{0}@{1}/"
                             "roundcubemail\'\" {2}roundcubemail"
                             "/htdocs/config/config."
                             "inc.php"
                             .format(rc_passwd,
                                     EEVariables.ee_mysql_host,
                                     EEVariables.ee_webroot))

        # Sieve plugin configuration in roundcube
        EEShellExec.cmd_exec(self, "bash -c \"sed -i \\\"s:\$config\["
                             "\'plugins\'\] "
                             "= array(:\$config\['plugins'\] =  "
                             "array(\\n    \'sieverules\',:\\\" "
                             "{0}roundcubemail/htdocs/config"
                             .format(EEVariables.ee_webroot)
                             + "/config.inc.php\"")
        EEShellExec.cmd_exec(self, "echo \"\$config['sieverules_port']"
                             "=4190;\" >> {0}roundcubemail"
                             .format(EEVariables.ee_webroot)
                             + "/htdocs/config/config.inc.php")

        data = dict(site_name='webmail', www_domain='webmail',
                    static=False,
                    basic=True, wp=False, w3tc=False, wpfc=False,
                    wpsc=False, multisite=False, wpsubdir=False,
                    webroot=EEVariables.ee_webroot, ee_db_name='',
                    ee_db_user='', ee_db_pass='', ee_db_host='',
                    rc=True)

        self.log.debug(self, 'Writting the nginx configuration for '
                  'RoundCubemail')
        ee_rc = open('/etc/nginx/sites-available/webmail',
                     encoding='utf-8', mode='w')
        app.render((data), 'virtualconf.mustache',
                        out=ee_rc)
        ee_rc.close()


    def _remove_vimbadmin(self):
        """
        Remove Vimbadmin Stack 
        """
        self.log.info("Removing Vimbadmin, please wait...")
        # Remove Vimbadmin database
        if EEShellExec.cmd_exec(self, "mysqladmin ping"):
            EEMysql.execute(self, "drop database IF EXISTS vimbadmin")

        # Remove Vimbadmin
        if EEFileUtils.isexist(self, "{0}22222/htdocs/vimbadmin"
                                .format(EEVariables.ee_webroot)):
            EEFileUtils.remove(self, ["{0}22222/htdocs/vimbadmin".format(EEVariables.ee_webroot)])

    def _remove_roundcube(self):
        """
        Remove Roundcube Stack 
        """

        self.log.info("Removing Roundcube, please wait...")
        # Remove Roundcube database
        if EEShellExec.cmd_exec(self, "mysqladmin ping"):
            EEMysql.execute(self, "drop database IF EXISTS roundcubemail")

        # Remove Roundcube files
        if EEFileUtils.isexist(self, "{0}roundcubemail".format(EEVariables.ee_webroot)):
            EEFileUtils.remove(self, ["{0}roundcubemail".format(EEVariables.ee_webroot)])


    def _pre_install_stack(self):
        """
        Defines pre-install activities done before installing mail stack
        """
        # Add mail repository

        self._requirement_check()
        self._add_repo()

        self.log.debug(self, 'Executing the command debconf-set-selections.')
        try:
            EEShellExec.cmd_exec(self, "echo \"dovecot-core dovecot-core/"
                                 "create-ssl-cert boolean yes\" "
                                 "| debconf-set-selections")
            EEShellExec.cmd_exec(self, "echo \"dovecot-core dovecot-core"
                                 "/ssl-cert-name string $(hostname -f)\""
                                 " | debconf-set-selections")
        except CommandExecutionError as e:
            self.log.error("Failed to initialize dovecot packages")

    def _post_install_stack(self):
        """
        Defines activities done after installing mail stack
        """
        self.log.debug(self, "Adding user")
        try:
            EEShellExec.cmd_exec(self, "adduser --uid 5000 --home /var"
                                 "/vmail --disabled-password --gecos "
                                 "'' vmail")
        except CommandExecutionError as e:
            self.log.error(self, "Unable to add vmail user for mail server")
        try:
            EEShellExec.cmd_exec(self, "openssl req -new -x509 -days"
                                 " 3650 "
                                 "-nodes -subj /commonName={hostname}"
                                 "/emailAddress={email} -out /etc/ssl"
                                 "/certs/dovecot."
                                 "pem -keyout "
                                 "/etc/ssl/private/dovecot.pem"
                                 .format(hostname=EEVariables.ee_fqdn,
                                         email=EEVariables.ee_email))
        except CommandExecutionError as e:
            self.log.error(self, "Unable to generate PEM key for dovecot")
        self.log.debug(self, "Setting Privileges to "
                  "/etc/ssl/private/dovecot.pem file ")
        EEFileUtils.chmod(self, "/etc/ssl/private/dovecot.pem", 0o600)

        # Custom Dovecot configuration by EasyEngine
        data = dict()
        self.log.debug(self, "Writting configuration into file"
                  "/etc/dovecot/conf.d/auth-sql.conf.ext ")
        ee_dovecot = open('/etc/dovecot/conf.d/auth-sql.conf.ext',
                          encoding='utf-8', mode='w')
        app.render((data), 'auth-sql-conf.mustache',
                        out=ee_dovecot)
        ee_dovecot.close()

        data = dict(email=EEVariables.ee_email)
        self.log.debug(self, "Writting configuration into file"
                  "/etc/dovecot/conf.d/99-ee.conf ")
        ee_dovecot = open('/etc/dovecot/conf.d/99-ee.conf',
                          encoding='utf-8', mode='w')
        app.render((data), 'dovecot.mustache', out=ee_dovecot)
        ee_dovecot.close()
        try:
            EEShellExec.cmd_exec(self, "sed -i \"s/\\!include "
                                 "auth-system.conf.ext/#\\!include "
                                 "auth-system.conf.ext/\" "
                                 "/etc/dovecot/conf.d/10-auth.conf")

            EEShellExec.cmd_exec(self, "sed -i \"s\'/etc/dovecot/"
                                 "dovecot.pem\'/etc/ssl/certs/"
                                 "dovecot.pem"
                                 "\'\" /etc/dovecot/conf.d/"
                                 "10-ssl.conf")
            EEShellExec.cmd_exec(self, "sed -i \"s\'/etc/dovecot/"
                                 "private/dovecot.pem\'/etc/ssl/"
                                 "private"
                                 "/dovecot.pem\'\" /etc/dovecot/"
                                 "conf.d/"
                                 "10-ssl.conf")

            # Custom Postfix configuration needed with Dovecot
            # Changes in master.cf
            # TODO: Find alternative for sed in Python
            EEShellExec.cmd_exec(self, "sed -i \'s/#submission/"
                                 "submission/\'"
                                 " /etc/postfix/master.cf")
            EEShellExec.cmd_exec(self, "sed -i \'s/#smtps/smtps/\'"
                                 " /etc/postfix/master.cf")

            EEShellExec.cmd_exec(self, "postconf -e \"smtpd_sasl_type "
                                 "= dovecot\"")
            EEShellExec.cmd_exec(self, "postconf -e \"smtpd_sasl_path "
                                 "= private/auth\"")
            EEShellExec.cmd_exec(self, "postconf -e \""
                                 "smtpd_sasl_auth_enable = "
                                 "yes\"")
            EEShellExec.cmd_exec(self, "postconf -e \""
                                 " smtpd_relay_restrictions ="
                                 " permit_sasl_authenticated, "
                                 " permit_mynetworks, "
                                 " reject_unauth_destination\"")

            EEShellExec.cmd_exec(self, "postconf -e \""
                                 "smtpd_tls_mandatory_"
                                 "protocols = !SSLv2,!SSLv3\"")
            EEShellExec.cmd_exec(self, "postconf -e \"smtp_tls_"
                                 "mandatory_protocols = !SSLv2,"
                                 "!SSLv3\"")
            EEShellExec.cmd_exec(self, "postconf -e \"smtpd_tls"
                                 "_protocols = !SSLv2,!SSLv3\"")
            EEShellExec.cmd_exec(self, "postconf -e \"smtp_tls"
                                 "_protocols = !SSLv2,!SSLv3\"")
            EEShellExec.cmd_exec(self, "postconf -e \"mydestination "
                                 "= localhost\"")
            EEShellExec.cmd_exec(self, "postconf -e \"virtual"
                                 "_transport "
                                 "= lmtp:unix:private/dovecot-lmtp\"")
            EEShellExec.cmd_exec(self, "postconf -e \"virtual_uid_"
                                 "maps = static:5000\"")
            EEShellExec.cmd_exec(self, "postconf -e \"virtual_gid_"
                                 "maps = static:5000\"")
            EEShellExec.cmd_exec(self, "postconf -e \""
                                 " virtual_mailbox_domains = "
                                 "mysql:/etc/postfix/mysql/virtual_"
                                 "domains_maps.cf\"")
            EEShellExec.cmd_exec(self, "postconf -e \"virtual_mailbox"
                                 "_maps"
                                 " = mysql:/etc/postfix/mysql/virtual_"
                                 "mailbox_maps.cf\"")
            EEShellExec.cmd_exec(self, "postconf -e \"virtual_alias"
                                 "_maps  "
                                 "= mysql:/etc/postfix/mysql/virtual_"
                                 "alias_maps.cf\"")
            EEShellExec.cmd_exec(self, "openssl req -new -x509 -days "
                                 " 3650 -nodes -subj /commonName="
                                 "{hostname}/emailAddress={email}"
                                 " -out /etc/ssl/certs/postfix.pem"
                                 " -keyout /etc/ssl/private/"
                                 "postfix.pem"
                                 .format(hostname=EEVariables.ee_fqdn,
                                         email=EEVariables.ee_email))
            EEShellExec.cmd_exec(self, "chmod 0600 /etc/ssl/private"
                                 "/postfix.pem")
            EEShellExec.cmd_exec(self, "postconf -e \"smtpd_tls_cert_"
                                 "file = /etc/ssl/certs/postfix.pem\"")
            EEShellExec.cmd_exec(self, "postconf -e \"smtpd_tls_key_"
                                 "file = /etc/ssl/private/"
                                 "postfix.pem\"")

        except CommandExecutionError as e:
            self.log.error(self, "Failed to update Dovecot configuration")

        # Sieve configuration
        if not os.path.exists('/var/lib/dovecot/sieve/'):
            self.log.debug(self, 'Creating directory '
                      '/var/lib/dovecot/sieve/ ')
            os.makedirs('/var/lib/dovecot/sieve/')

        # Custom sieve configuration by EasyEngine
        data = dict()
        self.log.debug(self, "Writting configuration of EasyEngine into "
                  "file /var/lib/dovecot/sieve/default.sieve")
        ee_sieve = open('/var/lib/dovecot/sieve/default.sieve',
                        encoding='utf-8', mode='w')
        app.render((data), 'default-sieve.mustache',
                        out=ee_sieve)
        ee_sieve.close()

        # Compile sieve rules
        self.log.debug(self, "Setting Privileges to dovecot ")
        # EEShellExec.cmd_exec(self, "chown -R vmail:vmail /var/lib"
        #                     "/dovecot")
        EEFileUtils.chown(self, "/var/lib/dovecot", 'vmail', 'vmail',
                          recursive=True)
        try:
            EEShellExec.cmd_exec(self, "sievec /var/lib/dovecot/"
                                 "/sieve/default.sieve")
        except CommandExecutionError as e:
            raise SiteError("Failed to compile default.sieve")

        EEGit.add(self, ["/etc/postfix", "/etc/dovecot"],
                  msg="Installed mail server")
        EEService.restart_service(self, 'dovecot')
        EEService.reload_service(self, 'postfix')

    def install_stack(self):
        """
        Install MAIL stack
        """
        self.log.info("Installing MAIL stack, please wait...")
        self._set_stack()
        self._pre_install_stack()

        if self.apt_packages:
            super(EEMailStack, self).install_stack()
            self._post_install_stack()

        if self.manual_packages:
            for key in self.manual_packages.keys():
                path = EEDownload(('%s' %key), self.manual_packages[key]).download()
                print("Evaluating function %s..." %key)
                print("self._install_{0}(self, '{1}')".format(key, path))
                eval("self._install_{0}('{1}')".format(key, path))
        
    def remove_stack(self):
        """
        Remove MAIL stack
        """
        self.log.info("Removing MAIL stack, please wait...")
        self._set_stack()
        if self.apt_packages:
          super(EEMailStack, self).remove_stack()
        if self.manual_packages:
          for key in self.manual_packages.keys():
              print("Evaluating function %s..." %key)
              print("self._remove_{0}(self)".format(key))
              eval("self._remove_{0}()".format(key))

    def purge_stack(self):
        self.log.info("Purging MAIL stack, please wait...")
        self._set_stack()
        if self.apt_packages:
          super(EEMailStack, self).purge_stack()
        if self.manual_packages:
          for key in self.manual_packages.keys():
              print("Evaluating function %s..." %key)
              print("self._remove_{0}(self)".format(key))
              eval("self._remove_{0}()".format(key))
