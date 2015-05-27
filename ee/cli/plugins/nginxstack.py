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


class EENginxStack(EEStack):
    """
        EasyEngine NGINX stack
    """
    packages_name = EEVariables.ee_nginx
    log = app.log

    def __init__(self, packages_name=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        """

        self.packages_name = self._get_stack()  
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
        pass

    def install_stack(self):
        """
        Install NGINX stack
        """
        self.log.info("Installing NGINX stack, please wait...")
        self._pre_install_stack()
        super(EENginxStack, self).install_stack()
        self._post_install_stack()

    def remove_stack(self):
        """
        Remove NGINX stack
        """
        self.log.info("Removing NGINX stack, please wait...")
        super(EENginxStack, self).remove_stack()

    def purge_stack(self):
        self.log.info("Purging NGINX stack, please wait...")
        super(EENginxStack, self).purge_stack()
