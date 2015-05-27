import os
import sys
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.core.apt_repo import EERepo
from ee.cli.plugins.eestack import EEStack
from ee.cli.main import app

class EEHhvmStack(EEStack):
    """
        EasyEngine HHVM stack
    """
    packages_name = EEVariables.ee_hhvm
    log = app.log

    def __init__(self, packages_name=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        """

        self.packages_name = self._get_stack()  
        super(EEHhvmStack, self).__init__(self.packages_name)

    def _get_stack(self):
        return EEHhvmStack.packages_name

    def _add_repo(self):
        """
          Add repository for packages to be downloaded from
        """
        self.log.info("Adding HHVM repository, please wait...")
        if (EEVariables.ee_platform_codename == 'precise'):
            self.log.debug(self, 'Adding PPA for Boost')
            EERepo.add(self, ppa=EEVariables.ee_boost_repo)

        self.log.debug(self, 'Adding ppa repo for HHVM')
        EERepo.add(self, repo_url=EEVariables.ee_hhvm_repo)
        self.log.debug(self, 'Adding HHVM GPG Key')
        EERepo.add_key(self, '0x5a16e7281be7a449')
        EEAptGet.update(self)

    def _pre_install_stack(self):
        """
        Defines pre-install activities done before installing hhvm stack
        """
        # Add hhvm repository
        self._add_repo()

    def _post_install_stack(self):
        """
        Defines activities done after installing hhvm stack
        """
        pass

    def install_stack(self):
        """
        Install HHVM stack
        """
        self.log.info("Installing HHVM stack, please wait...")
        self._pre_install_stack()
        super(EEHhvmStack, self).install_stack()
        self._post_install_stack()

    def remove_stack(self):
        """
        Remove HHVM stack
        """
        self.log.info("Removing HHVM stack, please wait...")
        super(EEHhvmStack, self).remove_stack()

    def purge_stack(self):
        self.log.info("Purging HHVM stack, please wait...")
        super(EEHhvmStack, self).purge_stack()
