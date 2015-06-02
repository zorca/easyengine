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
from ee.core.download import EEDownload
from ee.core.logging import Log
from ee.cli.main import app


class EEMysqlStack(EEStack):
    """
        EasyEngine MYSQL stack
    """
    packages_name = ["mariadb-server", "percona-toolkit"]
    app = app
    log = app.log

    def __init__(self, packages_name=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        """

        self.packages_name = self._get_stack()  
        super(EEMysqlStack, self).__init__(self.packages_name)

    def _get_stack(self):
        return EEMysqlStack.packages_name

    def _add_repo(self):
        """
          Add repository for packages to be downloaded from
        """
        self.log.info("Adding MySQL repository, please wait...")
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
        EEAptGet.update(self)

    def setup_mysqltuner(self):
      """

      """
      EEDownload.download(self, [["https://raw.githubusercontent.com/"
                                  "major/MySQLTuner-perl"
                                  "/master/mysqltuner.pl",
                                  "/usr/bin/mysqltuner", "MySQLTuner"]])
      # Set MySQLTuner permission
      EEFileUtils.chmod(self, "/usr/bin/mysqltuner", 0o775)



    def _pre_install_stack(self):
        """
        Defines pre-install activities done before installing mysql stack
        """
        self._add_repo()
        # Predefine MySQL Credentials
        chars = ''.join(random.sample(string.ascii_letters, 8))
        self.log.info("Pre-seeding MySQL")
        self.log.debug("echo \"mariadb-server-10.0 "
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
            self.log.error("Failed to initialize MySQL package")

        # Predefine MySQL credentials
        self.log.debug("echo \"mariadb-server-10.0 "
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
            self.log.error("Failed to initialize MySQL package")

        # Write ~/.my.cnf configuration
        mysql_config = """
        [client]
        user = root
        password = {chars}
        """.format(chars=chars)
        config = configparser.ConfigParser()
        config.read_string(mysql_config)
        self.log.debug('Writting configuration into MySQL file')
        with open(os.path.expanduser("~")+'/.my.cnf', encoding='utf-8',
                  mode='w') as configfile:
            config.write(configfile)

    def _post_install_stack(self):
        """
        Defines activities done after installing mysql stack
        """
        self.setup_mysqltuner()
        if not os.path.isfile("/etc/mysql/my.cnf"):
            config = ("[mysqld]\nwait_timeout = 30\n"
                      "interactive_timeout=60\nperformance_schema = 0"
                      "\nquery_cache_type = 1")
            config_file = open("/etc/mysql/my.cnf",
                               encoding='utf-8', mode='w')
            config_file.write(config)
            config_file.close()
        else:
            try:
                EEShellExec.cmd_exec(self, "sed -i \"/#max_conn"
                                     "ections/a wait_timeout = 30 \\n"
                                     "interactive_timeout = 60 \\n"
                                     "performance_schema = 0\\n"
                                     "query_cache_type = 1 \" "
                                     "/etc/mysql/my.cnf")
            except CommandExecutionError as e:
                Log.error(self, "Unable to update MySQL file")

        EEGit.add(self, ["/etc/mysql"], msg="Adding MySQL into Git")
        EEService.reload_service(self, 'mysql')

    def install_stack(self):
        """
        Install MYSQL stack
        """
        self.log.info("Installing MySQL stack, please wait...")
        self._pre_install_stack()
        super(EEMysqlStack, self).install_stack()
        self._post_install_stack()

    def remove_stack(self):
        """
        Remove MYSQL stack
        """
        self.log.info("Removing MySQL stack, please wait...")
        super(EEMysqlStack, self).remove_stack()

    def purge_stack(self):
        self.log.info("Purging MySQL stack, please wait...")
        super(EEMysqlStack, self).purge_stack()

    def is_installed(self):
        self.log.info("Checking if mysql is installed")
        return EEShellExec.cmd_exec(self, "mysqladmin ping")

