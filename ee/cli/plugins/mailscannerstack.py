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


class EEMailScannerStack(EEStack):
    """
        EasyEngine MAILScanner stack
    """
    packages_name = EEVariables.ee_mailscanner
    app = app
    log = app.log

    def __init__(self, packages_name=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        """

        self.packages_name = self._get_stack()  
        super(EEMailScannerStack, self).__init__(self.packages_name)

    def _get_stack(self):
        return EEMailScannerStack.packages_name

    def _add_repo(self):
        """
          Add repository for packages to be downloaded from
        """
        self.log.info("Adding MAILScanner repository, please wait...")
        
        EEAptGet.update(self)

    def _pre_install_stack(self):
        """
        Defines pre-install activities done before installing mail stack
        """
        # Add mail repository
        self._add_repo()


    def _post_install_stack(self):
        """
        Defines activities done after installing mail stack
        """
        # Set up Custom amavis configuration
        data = dict()
        self.log.debug(self, "Configuring file /etc/amavis/conf.d"
                       "/15-content_filter_mode")
        ee_amavis = open('/etc/amavis/conf.d/15-content_filter_mode',
                         encoding='utf-8', mode='w')
        self.app.render((data), '15-content_filter_mode.mustache',
                        out=ee_amavis)
        ee_amavis.close()

        # Amavis ViMbadmin configuration
        if os.path.isfile("/etc/postfix/mysql/virtual_alias_maps.cf"):
            vm_host = os.popen("grep hosts /etc/postfix/mysql/virtual_"
                               "alias_maps.cf | awk \'{ print $3 }\' |"
                               " tr -d '\\n'").read()
            vm_pass = os.popen("grep password /etc/postfix/mysql/"
                               "virtual_alias_maps.cf | awk \'{ print "
                               "$3 }\' | tr -d '\\n'").read()

            data = dict(host=vm_host, password=vm_pass)
            vm_config = open('/etc/amavis/conf.d/50-user',
                             encoding='utf-8', mode='w')
            self.app.render((data), '50-user.mustache', out=vm_config)
            vm_config.close()

        # Amavis postfix configuration
        try:
            EEShellExec.cmd_exec(self, "postconf -e \"content_filter ="
                                 " smtp-amavis:[127.0.0.1]:10024\"")
            EEShellExec.cmd_exec(self, "sed -i \"s/1       pickup/1   "
                                 "    pickup"
                                 "\\n        -o content_filter=\\n    "
                                 "  -o receive_override_options="
                                 "no_header_body"
                                 "_checks/\" /etc/postfix/master.cf")
        except CommandExecutionError as e:
            raise SiteError("Failed to update Amavis-Postfix config")

        amavis_master = ("""smtp-amavis unix - - n - 2 smtp
-o smtp_data_done_timeout=1200
-o smtp_send_xforward_command=yes
-o disable_dns_lookups=yes
-o max_use=20
127.0.0.1:10025 inet n - n - - smtpd
-o content_filter=
-o smtpd_delay_reject=no
-o smtpd_client_restrictions=permit_mynetworks,reject
-o smtpd_helo_restrictions=
-o smtpd_sender_restrictions=
-o smtpd_recipient_restrictions=permit_mynetworks,reject
-o smtpd_data_restrictions=reject_unauth_pipelining
-o smtpd_end_of_data_restrictions=
-o smtpd_restriction_classes=
-o mynetworks=127.0.0.0/8
-o smtpd_error_sleep_time=0
-o smtpd_soft_error_limit=1001
-o smtpd_hard_error_limit=1000
-o smtpd_client_connection_count_limit=0
-o smtpd_client_connection_rate_limit=0
-o local_header_rewrite_clients=""")

        with open("/etc/postfix/master.cf",
                  encoding='utf-8', mode='a') as am_config:
                am_config.write(amavis_master)

        try:
            # Amavis ClamAV configuration
            self.log.debug(self, "Adding new user clamav amavis")
            EEShellExec.cmd_exec(self, "adduser clamav amavis")
            self.log.debug(self, "Adding new user amavis clamav")
            EEShellExec.cmd_exec(self, "adduser amavis clamav")
            self.log.debug(self, "Setting Privileges to /var/lib/amavis"
                      "/tmp")
            EEFileUtils.chmod(self, "/var/lib/amavis/tmp", 0o755)

            # Update ClamAV database
            self.log.debug(self, "Updating database")
            EEShellExec.cmd_exec(self, "freshclam")
        except CommandExecutionError as e:
            raise SiteError(" Unable to update ClamAV-Amavis config")

        # If Amavis is going to be installed then configure Vimabadmin
        # Amavis settings
        vm_config = open('/etc/amavis/conf.d/50-user',
                         encoding='utf-8', mode='w')
        self.app.render((data), '50-user.mustache',
                        out=vm_config)
        vm_config.close()

        EEGit.add(self, ["/etc/amavis"], msg="Adding Amavis into Git")
        EEService.restart_service(self, 'dovecot')
        EEService.reload_service(self, 'postfix')
        EEService.restart_service(self, 'amavis')


    def install_stack(self):
        """
        Install MAILScanner stack
        """
        self.log.info("Installing MAILScanner stack, please wait...")
        self._pre_install_stack()
        super(EEMailScannerStack, self).install_stack()
        self._post_install_stack()

    def remove_stack(self):
        """
        Remove MAILScanner stack
        """
        self.log.info("Removing MAILScanner stack, please wait...")
        super(EEMailScannerStack, self).remove_stack()

    def purge_stack(self):
        self.log.info("Purging MAILScanner stack, please wait...")
        super(EEMailScannerStack, self).purge_stack()