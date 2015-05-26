"""EasyEnging stack Interface"""




class EEStack(object):
    """
    This is meta description for EEStack
    """

    def __init__(self, package_name):
        """
            package_name: specify the name of package the operation 
                          to be performed on
        """
        self.package_name=package_name

    def install_stack(self, package_name):
        """
            Installs the package on system
        """
        pass

    def remove_stack(self, package_name):
        """
            Removes the package on system
        """
        pass

    def _is_installed(self, package_name):
        """
            Check if package is already installed
            Return
                True: if package is installed
                False: if package is not installed
        """
