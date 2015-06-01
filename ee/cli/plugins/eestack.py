"""EasyEnging stack Interface"""

from ee.core.aptget import EEAptGet


class EEStack(object):
    """
    This is meta description for EEStack
    """

    def __init__(self, package_name):
        """
            packages_name: specify the name of package the operation 
                          to be performed on
        """
        self.packages_name=package_name

    def install_stack(self):
        """
            Installs the package on system
        """
        print(self.packages_name)
        EEAptGet.install(self, self.packages_name)

    def remove_stack(self):
        """
            Removes the package on system
        """
        EEAptGet.remove(self, self.packages_name)
        EEAptGet.auto_remove(self)

    def purge_stack(self):
        """
            Purge the package from system
        """
        EEAptGet.remove(self, self.packages_name, purge=True)
        EEAptGet.auto_remove(self)

    def _is_installed(self):
        """
            Check if package is already installed
            Return
                True: if package is installed
                False: if package is not installed
        """
        result = dict()
        for package in self.packages_name():
            result.update({package: EEAptGet.is_installed(self, package)})
        return result