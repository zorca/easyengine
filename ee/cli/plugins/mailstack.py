import os
import sys
import random
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.cli.plugins.eestack import EEStack
from ee.core.shellexec import EEShellExec
from ee.core.shellexec import CommandExecutionError
from ee.core.fileutils import EEFileUtils
from ee.core.git import EEGit
from ee.core.services import EEService
from ee.core.logging import Log
from ee.cli.main import app


class EEMailStack(EEStack):
    """
        EasyEngine MAIL stack
    """
    packages_name = EEVariables.ee_mail
    app = app
    log = app.log

    def __init__(self, packages_name=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        """

        self.packages_name = self._get_stack()  
        super(EEMailStack, self).__init__(self.packages_name)

    def _get_stack(self):
        return EEMailStack.packages_name

    def _add_repo(self):
        """
          Add repository for packages to be downloaded from
        """
        self.log.info("Adding MAIL repository, please wait...")
        
        EEAptGet.update(self)

    def _pre_install_stack(self):
        """
        Defines pre-install activities done before installing mail stack
        """
        # Add mail repository
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
        self._pre_install_stack()
        super(EEMailStack, self).install_stack()
        self._post_install_stack()

    def remove_stack(self):
        """
        Remove MAIL stack
        """
        self.log.info("Removing MAIL stack, please wait...")
        super(EEMailStack, self).remove_stack()

    def purge_stack(self):
        self.log.info("Purging MAIL stack, please wait...")
        super(EEMailStack, self).purge_stack()
