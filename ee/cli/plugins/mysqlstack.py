import os
import random
import string
import configparser
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.core.apt_repo import EERepo
from ee.cli.plugins.eestack import EEStack
from ee.core.shellexec import EEShellExec

# from ee.core.logging import Log
from ee.cli.main import app


class EEMysqlStack(EEStack):
    """
        EasyEngine MYSQL stack
    """
    packages_name = ["mariadb-server", "percona-toolkit"]
    # log = app.log
    def __init__(self, packages_name=None):
        """
            Initialize packages list in stack
            pkgs_name: list of packages to be intialized for operations 
                        in stack
        """

        self.packages_name = self._get_stack()
  
        self.log = app.log
        print(self.packages_name)
        super(EEMysqlStack, self).__init__(self.packages_name)

    def _get_stack(self):
      return EEMysqlStack.packages_name


    def _pre_install_stack(self):
        """
            Defines pre-install activities done before installing mysql stack
        """

        mysql_pref = ("Package: *\nPin: origin mirror.aarnet.edu.au"
                      "\nPin-Priority: 1000\n")
        with open('/etc/apt/preferences.d/'
                  'MariaDB.pref', 'w') as mysql_pref_file:
            mysql_pref_file.write(mysql_pref)

        # Add repository
        if EEVariables.ee_platform_codename != 'jessie':
            EERepo.add(self, repo_url=EEVariables.ee_mysql_repo)
            self.log.debug('Adding key for {0}'
                      .format(EEVariables.ee_mysql_repo))
            EERepo.add_key(self, '0xcbcb082a1bb943db',
                           keyserver="keyserver.ubuntu.com")

        # Predefine MySQL Credentials
        chars = ''.join(random.sample(string.ascii_letters, 8))
        print("Pre-seeding MySQL")
        print("echo \"mariadb-server-10.0 "
                  "mysql-server/root_password "
                  "password \" | "
                  "debconf-set-selections")
        try:
            EEShellExec.cmd_exec(self, "echo \"mariadb-server-10.0 "
                                 "mysql-server/root_password "
                                 "password {chars}\" | "
                                 "debconf-set-selections"
                                 .format(chars=chars),
                                 log=False)
        except CommandExecutionError as e:
            print("Failed to initialize MySQL package")

        # Predefine MySQL credentials
        print("echo \"mariadb-server-10.0 "
                  "mysql-server/root_password_again "
                  "password \" | "
                  "debconf-set-selections")
        try:
            EEShellExec.cmd_exec(self, "echo \"mariadb-server-10.0 "
                                 "mysql-server/root_password_again "
                                 "password {chars}\" | "
                                 "debconf-set-selections"
                                 .format(chars=chars),
                                 log=False)
        except CommandExecutionError as e:

            print("Failed to initialize MySQL package")

        # Write ~/.my.cnf configuration
        mysql_config = """
        [client]
        user = root
        password = {chars}
        """.format(chars=chars)
        config = configparser.ConfigParser()
        config.read_string(mysql_config)
        print('Writting configuration into MySQL file')
        with open(os.path.expanduser("~")+'/.my.cnf', encoding='utf-8',
                  mode='w') as configfile:
            config.write(configfile)
        print("Done")

    def _post_install_stack(self):
        """
            Defines activities done after installing mysql stack
        """
        pass

    def install_stack(self):
        print("Installing MySQL stack")
        self._pre_install_stack()
        super(EEMysqlStack, self).install_stack()
        self._post_install_stack()

    def remove_stack(self):
        print("Removing MySQL stack")
        super(EEMysqlStack, self).remove_stack()

    def purge_stack(self):
        print("Purging MySQL stack")
        super(EEMysqlStack, self).purge_stack()
        print("Done")

