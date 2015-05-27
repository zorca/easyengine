import os
import sys
import random
import string
import configparser
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.core.apt_repo import EERepo
from ee.cli.plugins.eestack import EEStack
from ee.core.shellexec import EEShellExec
from ee.core.shellexec import CommandExecutionError
from ee.core.logging import Log
from ee.cli.main import app


class EEPhpStack(EEStack):
    """
        EasyEngine PHP stack
    """
    packages_name = EEVariables.ee_php
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
        pass

    def install_stack(self):
        """
        Install PHP stack
        """
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
