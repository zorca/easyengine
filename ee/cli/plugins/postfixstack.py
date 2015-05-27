import os
import sys
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.core.apt_repo import EERepo
from ee.cli.plugins.eestack import EEStack
from ee.core.shellexec import EEShellExec
from ee.core.services import EEService
from ee.core.git import EEGit
from ee.core.shellexec import CommandExecutionError
from ee.cli.main import app

class EEPostfixStack(EEStack):
    """
        EasyEngine Postfix stack
    """
    packages_name = EEVariables.ee_postfix
    log = app.log

    def __init__(self, packages_name=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        """

        self.packages_name = self._get_stack()  
        super(EEPostfixStack, self).__init__(self.packages_name)

    def _get_stack(self):
        return EEPostfixStack.packages_name

    def _add_repo(self):
        """
          Add repository for packages to be downloaded from
        """
        pass

    def _pre_install_stack(self):
        """
        Defines pre-install activities done before installing hhvm stack
        """
        # Add hhvm repository
        self._add_repo()

        self.log.debug(self, "Pre-seeding Postfix")
        try:
            EEShellExec.cmd_exec(self, "echo \"postfix postfix"
                                 "/main_mailer_type string \'Internet Site"
                                 "\'\""
                                 " | debconf-set-selections")
            EEShellExec.cmd_exec(self, "echo \"postfix postfix/mailname"
                                 " string $(hostname -f)\" | "
                                 "debconf-set-selections")
        except CommandExecutionError as e:
            self.log.error(self, "Failed to intialize postfix package")

    def _post_install_stack(self):
        """
        Defines activities done after installing hhvm stack
        """
        EEGit.add(self, ["/etc/postfix"],
                  msg="Adding Postfix into Git")
        EEService.reload_service(self, 'postfix')

    def install_stack(self):
        """
        Install Postfix stack
        """
        self.log.info("Installing Postfix stack, please wait...")
        self._pre_install_stack()
        super(EEPostfixStack, self).install_stack()
        self._post_install_stack()

    def remove_stack(self):
        """
        Remove Postfix stack
        """
        self.log.info("Removing Postfix stack, please wait...")
        super(EEPostfixStack, self).remove_stack()

    def purge_stack(self):
        self.log.info("Purging Postfix stack, please wait...")
        super(EEPostfixStack, self).purge_stack()
